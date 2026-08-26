#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software;
# you can redistribute it and/or modify it under the terms of the
# MIT License; see LICENSE file for more details.
#

from tathu.io import spatialite

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import networkx as nx
import random

def getPreviousRelationNode(family, timestamp):
    # Find closest previous system
    previous_index = None
    previous_timestamp = None
    for i in range(len(family.systems)):
        system = family.systems[i]
        if system.timestamp < timestamp:
            if previous_timestamp is None or \
               system.timestamp > previous_timestamp:
                previous_timestamp = system.timestamp
                previous_index = i

    # Previous system not found
    if previous_index is None:
        return None

    return (
        family.name,
        previous_index
    )

def buildGraphHistory(family, G):
    global visited_families

    # First node of this family
    first_node = (family.name, 0)

    # Family already processed
    if family.name in visited_families:
        return first_node

    visited_families.append(family.name)

    # Get centroids
    centroids = family.getCentroids()

    # Add all family nodes
    for i in range(len(family.systems)):
        # Get current system
        system = family.systems[i]

        # Unique node identifier
        node = (family.name, i)

        # Label only first node of family
        label = None

        if i == 0:
            label = str(family.name)[0:4]

        # Add node
        G.add_node(
            node,
            family=family.name,
            index=i,
            timestamp=system.timestamp,
            event=str(system.event),
            label=label
        )

        # Set geographic position
        G.position[node] = centroids[i]

    # Add temporal relationships inside family
    for i in range(1, len(family.systems)):
        # Current node
        node = (family.name, i)

        # Previous node
        previous = (family.name, i - 1)

        # Add temporal edge
        G.add_edge(
            previous,
            node,
            relation='temporal',
            event=None
        )

    # Add relationships between families
    for i in range(len(family.systems)):
        # Get current system
        system = family.systems[i]

        # Current node
        node = (family.name, i)

        # Recursion relationships
        for f in system.relationships:
            relation = db.load(
                str(f),
                ['min', 'mean', 'std', 'count']
            )

            # Build related family
            buildGraphHistory(
                relation,
                G
            )

            # Find the related system immediately
            # before the current system
            relation_node = getPreviousRelationNode(
                relation,
                system.timestamp
            )

            # Get life cycle event
            event = str(system.event)

            # Only SPLIT and MERGE represent
            # relationships between families
            edge_event = None

            if event in ['SPLIT', 'MERGE']:
                edge_event = event

            # Connect related previous system
            # to current system
            if relation_node is not None and \
               relation_node in G:
                G.add_edge(
                    relation_node,
                    node,
                    relation='family',
                    event=edge_event
                )

    return first_node

def getHistoryPosition(G):
    # Family vertical position
    family_position = {
        family_name: i
        for i, family_name in enumerate(visited_families)
    }

    # Create positions
    position = {}

    for node, data in G.nodes(data=True):
        # Convert timestamp to matplotlib date
        timestamp = mdates.date2num(
            data['timestamp']
        )
        position[node] = (
            timestamp,
            family_position[data['family']]
        )

    return position

def getElapsedTime(G):
    # Get focal family
    focal_family = visited_families[0]

    # Get initial timestamp of focal family
    start = min(
        data['timestamp']
        for node, data in G.nodes(data=True)
        if data['family'] == focal_family
    )

    # Create elapsed time dictionary
    elapsed = {}

    for node, data in G.nodes(data=True):
        elapsed[node] = (
            data['timestamp'] - start
        ).total_seconds() / 60.0

    return elapsed

def getEdges(G):
    # Temporal edges
    temporal_edges = [
        (u, v)
        for u, v, data in G.edges(data=True)
        if data['relation'] == 'temporal'
    ]

    # Relationships between families
    family_edges = [
        (u, v)
        for u, v, data in G.edges(data=True)
        if data['relation'] == 'family'
    ]

    return temporal_edges, family_edges

def drawNodes(G, position, family_colors, ax):
    # Draw each family using a different color
    for family_name in visited_families:
        # Normal nodes
        normal_nodes = [
            node
            for node, data in G.nodes(data=True)
            if data['family'] == family_name
            and data.get('event') != 'SPLIT'
        ]

        # Split nodes
        split_nodes = [
            node
            for node, data in G.nodes(data=True)
            if data['family'] == family_name
            and data.get('event') == 'SPLIT'
        ]

        # Draw normal nodes
        if normal_nodes:
            nx.draw_networkx_nodes(
                G,
                position,
                nodelist=normal_nodes,
                node_color=family_colors[family_name],
                node_size=300,
                node_shape='o',
                alpha=0.5,
                ax=ax
            )

        # Draw split nodes
        if split_nodes:
            nx.draw_networkx_nodes(
                G,
                position,
                nodelist=split_nodes,
                node_color=family_colors[family_name],
                node_size=200,
                node_shape='D',
                alpha=0.8,
                ax=ax
            )

def drawFamilyLabels(G, position, ax):
    # Labels only for first node of each family
    labels = {
        node: data['label']
        for node, data in G.nodes(data=True)
        if data.get('label') is not None
    }

    nx.draw_networkx_labels(
        G,
        position,
        labels=labels,
        font_size=7,
        verticalalignment='bottom',
        ax=ax
    )

def drawEventLabels(G, position, ax):
    # Labels only for SPLIT and MERGE edges
    labels = {
        (u, v): data['event']
        for u, v, data in G.edges(data=True)
        if data.get('event') in ['SPLIT', 'MERGE']
    }

    nx.draw_networkx_edge_labels(
        G,
        position,
        edge_labels=labels,
        font_size=8,
        rotate=False,
        label_pos=0.5,
        ax=ax
    )

def configureHistoryAxis(G, ax):
    # Restore axes hidden by NetworkX drawing functions
    ax.set_axis_on()

    # Get timestamps
    timestamps = sorted(
        set(
            data['timestamp']
            for node, data in G.nodes(data=True)
        )
    )

    # Configure date locator
    locator = mdates.AutoDateLocator()

    ax.xaxis.set_major_locator(
        locator
    )

    # Configure timestamp format
    ax.xaxis.set_major_formatter(
        mdates.DateFormatter(
            '%d/%m %H:%M'
        )
    )

    # Ensure X axis is visible
    ax.xaxis.set_visible(True)

    ax.tick_params(
        axis='x',
        which='both',
        bottom=True,
        top=False,
        labelbottom=True
    )

    # Ensure Y axis is not visible
    ax.yaxis.set_visible(False)

    ax.tick_params(
        axis='y',
        which='both',
        left=True,
        right=False,
        labelleft=True
    )

    # Explicitly define temporal limits
    if timestamps:
        minimum = mdates.date2num(
            timestamps[0]
        )

        maximum = mdates.date2num(
            timestamps[-1]
        )

        # Add small horizontal margin
        margin = max(
            (maximum - minimum) * 0.03,
            1.0 / (24.0 * 60.0)
        )

        ax.set_xlim(
            minimum - margin,
            maximum + margin
        )

    # Rotate timestamp labels
    plt.setp(
        ax.get_xticklabels(),
        rotation=45,
        ha='right'
    )

def plotGraphHistory(G, family_colors, mode='geographic'):
    print('Mode', repr(mode))
    # Get edges
    temporal_edges, family_edges = getEdges(G)

    # Geographic visualization
    if mode == 'geographic':
        fig, ax = plt.subplots()

        position = G.position

        # Draw temporal edges
        nx.draw_networkx_edges(
            G,
            position,
            edgelist=temporal_edges,
            arrows=False,
            width=1.5,
            alpha=0.4,
            ax=ax
        )

        # Draw relationships between families
        nx.draw_networkx_edges(
            G,
            position,
            edgelist=family_edges,
            arrows=False,
            width=2.5,
            style='dashed',
            alpha=0.8,
            ax=ax
        )

        # Draw nodes
        drawNodes(
            G,
            position,
            family_colors,
            ax
        )

        # Draw family labels
        drawFamilyLabels(
            G,
            position,
            ax
        )

        # Draw event labels
        drawEventLabels(
            G,
            position,
            ax
        )

        ax.set_title('Geographic History')
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        ax.set_aspect('equal', adjustable='datalim')

    # Temporal / genealogical visualization
    elif mode == 'history':
        fig, ax = plt.subplots()

        # Get timestamp positions
        position = getHistoryPosition(G)

        # Draw temporal edges
        nx.draw_networkx_edges(
            G,
            position,
            edgelist=temporal_edges,
            arrows=False,
            width=1.5,
            alpha=0.4,
            ax=ax
        )

        # Draw relationships between families
        nx.draw_networkx_edges(
            G,
            position,
            edgelist=family_edges,
            arrows=False,
            width=2.5,
            style='dashed',
            alpha=0.8,
            ax=ax
        )

        # Draw nodes
        drawNodes(
            G,
            position,
            family_colors,
            ax
        )

        # Draw family labels
        drawFamilyLabels(
            G,
            position,
            ax
        )

        # Draw event labels
        drawEventLabels(
            G,
            position,
            ax
        )

        # Configure family axis
        ax.set_yticks(
            range(len(visited_families))
        )

        ax.set_yticklabels(
            [
                str(family_name)
                for family_name in visited_families
            ]
        )

        # Configure timestamp axis
        configureHistoryAxis(
            G,
            ax
        )

        ax.set_title('Family History')
        ax.set_xlabel('Timestamp')
        ax.set_ylabel('Family')

        ax.grid(
            axis='x',
            alpha=0.2
        )

    # Topological visualization
    elif mode == 'topology':
        fig, ax = plt.subplots()

        position = nx.kamada_kawai_layout(G)

        # Draw temporal edges
        nx.draw_networkx_edges(
            G,
            position,
            edgelist=temporal_edges,
            arrows=False,
            width=1.5,
            alpha=0.4,
            ax=ax
        )

        # Draw relationships between families
        nx.draw_networkx_edges(
            G,
            position,
            edgelist=family_edges,
            arrows=False,
            width=2.5,
            style='dashed',
            alpha=0.8,
            ax=ax
        )

        # Draw nodes
        drawNodes(
            G,
            position,
            family_colors,
            ax
        )

        # Draw family labels
        drawFamilyLabels(
            G,
            position,
            ax
        )

        # Draw event labels
        drawEventLabels(
            G,
            position,
            ax
        )

        ax.set_title('Graph Topology')
        ax.axis('off')

    # Space-time visualization
    elif mode == 'spacetime':
        fig = plt.figure()

        ax = fig.add_subplot(
            111,
            projection='3d'
        )

        # Get elapsed time
        elapsed = getElapsedTime(G)

        # Draw temporal edges
        for u, v in temporal_edges:
            x1, y1 = G.position[u]
            x2, y2 = G.position[v]

            z1 = elapsed[u]
            z2 = elapsed[v]

            ax.plot(
                [x1, x2],
                [y1, y2],
                [z1, z2],
                alpha=0.4
            )

        # Draw relationships between families
        for u, v in family_edges:
            x1, y1 = G.position[u]
            x2, y2 = G.position[v]

            z1 = elapsed[u]
            z2 = elapsed[v]

            ax.plot(
                [x1, x2],
                [y1, y2],
                [z1, z2],
                linestyle='dashed',
                linewidth=2.5,
                alpha=0.8
            )

            # Draw event label
            event = G.edges[u, v].get('event')

            if event in ['SPLIT', 'MERGE']:
                ax.text(
                    (x1 + x2) / 2.0,
                    (y1 + y2) / 2.0,
                    (z1 + z2) / 2.0,
                    event,
                    fontsize=8
                )

        # Draw each family using a different color
        for family_name in visited_families:
            # Normal nodes
            normal_nodes = [
                node
                for node, data in G.nodes(data=True)
                if data['family'] == family_name
                and data.get('event') != 'SPLIT'
            ]

            # Split nodes
            split_nodes = [
                node
                for node, data in G.nodes(data=True)
                if data['family'] == family_name
                and data.get('event') == 'SPLIT'
            ]

            # Draw normal nodes
            if normal_nodes:
                ax.scatter(
                    [
                        G.position[node][0]
                        for node in normal_nodes
                    ],
                    [
                        G.position[node][1]
                        for node in normal_nodes
                    ],
                    [
                        elapsed[node]
                        for node in normal_nodes
                    ],
                    color=family_colors[family_name],
                    marker='o',
                    s=100,
                    alpha=0.5
                )

            # Draw split nodes
            if split_nodes:
                ax.scatter(
                    [
                        G.position[node][0]
                        for node in split_nodes
                    ],
                    [
                        G.position[node][1]
                        for node in split_nodes
                    ],
                    [
                        elapsed[node]
                        for node in split_nodes
                    ],
                    color=family_colors[family_name],
                    marker='D',
                    s=130,
                    alpha=0.8
                )

            # First node of family
            first_node = (
                family_name,
                0
            )

            if first_node in G:
                x0, y0 = G.position[first_node]
                z0 = elapsed[first_node]

                ax.text(
                    x0,
                    y0,
                    z0,
                    str(family_name),
                    fontsize=7
                )

        ax.set_title('Space-time History')
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        ax.set_zlabel('Elapsed time (minutes)')

    else:
        raise ValueError(
            'Invalid visualization mode: {}'.format(mode)
        )

    plt.tight_layout()
    plt.show()

# Database connection
dbname = './data/databases/db-tracking-goes13_2017_12.sqlite'
table = 'systems'
db = spatialite.Loader(dbname, table)

# Get systems
names = db.loadNames()

# Load first family
family = db.load(
    names[random.randint(0, len(names) - 1)],
    ['min', 'mean', 'std', 'count']
)

for system in family.systems:
    print(
        system.name,
        system.timestamp,
        system.event,
        system.getRelationshipNamesAsString()
    )

# Build graph
G = nx.DiGraph()
G.position = {}
visited_families = []

buildGraphHistory(family, G)

# Colors
random.seed(42)

family_colors = {}
for family_name in visited_families:
    family_colors[family_name] = '#{:06x}'.format(
        random.randint(0, 0xffffff)
    )

# Plot graph
plotGraphHistory(
    G,
    family_colors,
    mode='history'
)
