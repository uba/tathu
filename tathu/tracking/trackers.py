#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

from tathu.geometry import transform
from tathu.tracking.system import ConvectiveSystemManager, LifeCycleEvent

### @begin-Overlap area strategies. ###

class OverlapAreaStrategy:
    def hasIntersection(self, current_system, previous_system):
        # Verify intersection
        intersection = current_system.geom.Intersection(previous_system.geom)
        if intersection.GetDimension() < 2:
            return False
        return intersection

    def hasRelationship(self, current_system, previous_system):
        raise NotImplementedError

class AbsoluteOverlapAreaStrategy(OverlapAreaStrategy):
    '''Absolute value strategy: it computes the intersection area
       and compares with the given area threshold.'''
    def __init__(self, threshold):
        self.threshold = threshold

    def hasRelationship(self, current_system, previous_system):
        # Verify intersection
        intersection = self.hasIntersection(current_system, previous_system)
        if intersection is False:
            return False

        # Compute area
        intersectionarea = intersection.GetArea()

        # Verify criterion
        if intersectionarea > self.threshold:
            return True

        return False

class RelativeOverlapAreaStrategy(OverlapAreaStrategy):
    ''''Relative value strategy: it computes the intersection area and
        compares with the area of current system using percent relation.'''
    def __init__(self, threshold):
        self.threshold = threshold

    def hasRelationship(self, current_system, previous_system):
        # Verify intersection
        intersection = self.hasIntersection(current_system, previous_system)
        if intersection is False:
            return False

        # Compute current area
        currentarea = current_system.geom.GetArea()

        # Compute intersection area
        intersectionarea = intersection.GetArea()

        # Compute %
        percent = intersectionarea / currentarea

        # Verify criterion
        if percent > self.threshold:
            return True

        return False

class TitanStrategy(OverlapAreaStrategy):
    ''' TITAN Strategy: Thunderstorm Identification, Tracking, Analysis and Nowcasting.
        More info: http://www.rap.ucar.edu/projects/titan/home/storm_tracking.php'''
    def __init__(self, threshold=0.5):
        self.threshold = threshold

    def hasRelationship(self, current_system, previous_system):
        # Verify intersection
        intersection = self.hasIntersection(current_system, previous_system)
        if intersection is False:
            return False

        # Compute old area
        oldarea = previous_system.geom.GetArea()

        # Compute current area
        currentarea = current_system.geom.GetArea()

        # Compute intersection area
        intersectionarea = intersection.GetArea()

        # Compute factors
        f1 = intersectionarea / oldarea
        f2 = intersectionarea / currentarea
        sum = f1 + f2

        # Verify criterion
        if sum >= self.threshold:
            return True

        return False

class IntersectsStrategy(OverlapAreaStrategy):
    def __init__(self):
        pass

    def hasRelationship(self, current_system, previous_system):
        return True

### @end-Overlap area strategies. ###

### @begin-System picker strategies. ###

def pick_system_by_max_area(systems):
    choosen, maxarea = None, 0.0
    for system in systems:
        area = system.geom.GetArea()
        if area > maxarea:
            choosen, maxarea = system, area
    return choosen

def pick_system_by_max_intensity(systems):
    choosen, maxval = None, 0.0
    for system in systems:
        val = system.raster.max()
        if val > maxval:
            choosen, maxval = system, val
    return choosen

### @end-System picker strategies. ###

class OverlapAreaTracker(object):
    '''
    This class implements a convective system tracker that uses the overlap area criterion.
    '''
    def __init__(self, previous, strategy, picker=pick_system_by_max_area):
        self.previous = previous # Set of previous systems at time.
        self.strategy = strategy # The overlap area strategy that will be used.
        self.picker = picker     # System picker strategy that will be used.

    def track(self, current):
        # Indexing previous convective cells
        manager = ConvectiveSystemManager(self.previous)

        # Candidates to SPLIT (previous system name -> current system)
        splits = {}

        # Merge (current system name -> previous system)
        merges = {}

        # Merged systems
        merged = {}

        # For each current system
        for sys in current:

            # Get previous systems that overlaps the current system
            overlaps = manager.getSystemsFromSystem(sys)

            # Used to store the relationships for each system
            relationships = []

            # For each overlap
            for over in overlaps:
                if self.strategy.hasRelationship(sys, over) is True:
                    relationships.append(over)

            # Store relationships for current system
            sys.relationships = relationships

            ### Classify life-cycle event ###

            # case len(relationships) == 0 -> It is SPONTANEOUS_GENERATION

            if len(relationships) == 1:
                # It is CONTINUITY or SPLIT
                # Get previous system name (identifier)
                name = relationships[0].name

                # First time that it is used?
                if name not in splits:
                    # If yes, it is CONTINUITY relationship
                    sys.event = LifeCycleEvent.CONTINUITY
                    # Store for future adjustments, if necessary
                    splits[name] = [sys]
                else:
                    # If not, it is SPLIT relationship
                    # Adjust the system that was considered as CONTINUITY
                    splits[name][0].event = LifeCycleEvent.SPLIT
                    # Set the current system class
                    sys.event = LifeCycleEvent.SPLIT
                    # Store for future adjustments, if necessary
                    splits[name].append(sys)

            elif len(relationships) >= 2:
                # It is MERGE
                sys.event = LifeCycleEvent.MERGE
                # Store
                merges[sys.name] = relationships
                merged[sys.name] = sys

        # Test: using for adjustments
        event_analysis = {}

        ### Adjust history (relations) ###
        for name in splits:
            # Get system on current time based on past time
            systems = splits[name]
            # It is CONTINUITY
            if len(systems) == 1:
                systems[0].name = name
                event_analysis[name] = [systems[0]]
            else:
                # Which system is chosen to continue
                # the previous system life cycle?
                choosen = self.__assignIdentifier(name, systems)
                event_analysis[name] = [choosen]

        for name in merges:
            # Get system on past time based on current time
            systems = merges[name]
            # Get name that will be followed
            choosen = self.__getIdentifier(systems)
            # Verify if used already
            if choosen in event_analysis:
                event_analysis[choosen].append(merged[name])
            else:
                event_analysis[choosen] = [merged[name]]

        # Here we have systems with same name. Choose by maximum area
        for key, systems in event_analysis.items():
            if len(systems) == 1:
                systems[0].name = key
            else:
                choosen = 0
                maxarea = 0.0
                for i in range(0, len(systems)):
                    area = systems[i].geom.GetArea()
                    if area > maxarea:
                        choosen = i
                        maxarea = area
                        systems[i].name = key

                for i in range(0, len(systems)):
                    if i != choosen:
                        current.remove(systems[i])

    def __assignIdentifier(self, name, relations):
        choosen = self.picker(relations)
        choosen.name = name # Baptized!
        return choosen

    def __getIdentifier(self, relations):
        choosen = self.picker(relations)
        return choosen.name

class EdgeTracker(object):
    '''
    This class implements a convective system tracker that verifies topology at edges.
    It can be used on global data, e.g. mosaic of satellite images covering the Earth territory.
    '''
    def __init__(self, previous):
        self.previous = previous

    def track(self, current):
        # Get previous touching right/left systems
        previous_right, previous_left = self.__getEdgeTouching(self.previous)

        # Get current touching right/left systems
        current_right, current_left = self.__getEdgeTouching(current)

        # Verify going from right to -> left
        self.__verifyTopology(previous_right, current_left)

        # Verify going from left to -> right
        self.__verifyTopology(previous_left, current_right)

    def __getEdgeTouching(self, systems):
        right, left = [], []
        for s in systems:
            if s.attrs['touching_right']:
                right.append(s)
            if s.attrs['touching_left']:
                left.append(s)
        return right, left

    def __verifyTopology(self, source, destination):
        for s in source:
            # Spinning around the world
            translated = transform.translate(s.geom, -360.0, 0.0)
            # Verify topology, assign name and build new geometry
            for d in destination:
                if translated.Touches(d.geom):
                    d.name = s.name # Baptized!
                    d.geom = d.geom.Union(translated)

class InsertDurationClusters():
    '''
    This class inserts the time position of the clusters since their detection
    '''
    def __init__(self, scale='seconds'):
        self.scale=scale

    def insert(self, current):
        for c in current:
            if c.event == LifeCycleEvent.SPONTANEOUS_GENERATION:
                pass
            else:
                c.duration = (c.timestamp - c.relationships[0].timestamp).seconds + c.relationships[0].duration
