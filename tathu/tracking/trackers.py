#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

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

class OverlapAreaTracker(object):
    '''
    This class implements a convective system tracker that uses the overlap area criterion.
    '''
    def __init__(self, previous, strategy):
        self.previous = previous # Set of previous systems at time.
        self.strategy = strategy # The overlap area strategy that will be used.

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

            if(len(relationships) == 1):
                # It is CONTINUITY or SPLIT
                # Get previous system name (identifier)
                name = relationships[0].name

                # First time that it is used?
                if(name not in splits):
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

            elif(len(relationships) >= 2):
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
            if(len(systems) == 1):
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
                    if(area > maxarea):
                        choosen = i
                        maxarea = area
                        systems[i].name = key

                for i in range(0, len(systems)):
                    if(i != choosen):
                        current.remove(systems[i])

    def __assignIdentifier(self, name, relations):
        '''
        This methods assigns identifier using maximum area criterion.
        '''
        choosen = None
        maxarea = 0.0
        for member in relations:
            area = member.geom.GetArea()
            if(area > maxarea):
                choosen = member
                maxarea = area

        # Baptized!
        choosen.name = name

        return choosen

    def __getIdentifier(self, relations):
        '''
        This methods returns the identifier using maximum area criterion.
        '''
        choosen = None
        maxarea = 0.0
        for member in relations:
            area = member.geom.GetArea()
            if(area > maxarea):
                choosen = member
                maxarea = area

        return choosen.name
