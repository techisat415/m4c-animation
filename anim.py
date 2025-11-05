from manim import *
import math, random
import numpy as np

class CurvedSmallWorld(Scene):
    def construct(self):

        self.camera.background_color = "#000000"

        N = 60               # number of nodes
        radius = 3           # circle radius
        rewire_fraction = 0.059   # fraction of total edges to rewire (0 = lattice, 1 = random)


        nodes = [
            Dot(radius=0.09, color=WHITE).move_to(radius * np.array([math.cos(2*PI*i/N), math.sin(2*PI*i/N), 0]))
            for i in range(N)
        ]

        # Animate node appearance
        self.play(
            LaggedStart(*[FadeIn(node, scale=0.3) for node in reversed(nodes)], lag_ratio=0.06)
        )
        self.wait(5.5)

        def arc_connection(i, j, color=WHITE, curvature=0.5, stroke_width=2):
            p1, p2 = nodes[i].get_center(), nodes[j].get_center()
            center = np.array([0, 0, 0])
            angle = curvature if np.cross(p1-center, p2-center)[2] > 0 else -curvature
            return ArcBetweenPoints(p1, p2, angle=angle, color=color, stroke_width=stroke_width)

        # adjacency set and edge map
        adjacency = {i: set() for i in range(N)}
        edge_map = {}
        edges_list = []

        for i in range(N):
            for hop in [1, 2]:  # 1-hop (adjacent), 2-hop (alternate)
                target = (i + hop) % N
                key = (min(i, target), max(i, target))
                if key in edge_map:
                    continue

                # Distinguish curvatures for visual clarity
                if hop == 1:
                    curvature = 0
                else:
                    curvature = -2

                edge = arc_connection(i, target, color=WHITE, curvature=curvature)
                edges_list.append(edge)
                edge_map[key] = edge
                adjacency[i].add(target)
                adjacency[target].add(i)

        # Display lattice edges
        edge_group = VGroup(*edges_list)
        self.play(Create(edge_group), run_time=1.2)
        self.wait(7.5)



        total_edges = len(edge_map)
        num_rewires = int(total_edges * rewire_fraction)
        all_edges = list(edge_map.keys())
        random.shuffle(all_edges)
        edges_to_rewire = all_edges[:num_rewires]

        removed_edges = []
        new_edges = []

        for (a, b) in edges_to_rewire:
            if (a, b) not in edge_map:
                continue

            old_edge = edge_map.pop((a, b))
            removed_edges.append(FadeOut(old_edge))

            adjacency[a].discard(b)
            adjacency[b].discard(a)

            possible_targets = [x for x in range(N) if x != a and x not in adjacency[a]]
            if not possible_targets:
                continue
            new_target = random.choice(possible_targets)
            new_key = (min(a, new_target), max(a, new_target))
            if new_key in edge_map:
                continue

            new_edge = arc_connection(a, new_target, color=WHITE, curvature=-1.2)
            new_edges.append(Create(new_edge))
            edge_map[new_key] = new_edge
            adjacency[a].add(new_target)
            adjacency[new_target].add(a)

        # Animate rewiring
        self.play(*removed_edges, *new_edges, run_time=2)
        self.wait(10.5)

                # === Show how distance between opposite nodes changes ===
        src, dst = 0, N // 2  # diametrically opposite nodes
        src_dot = nodes[src]
        dst_dot = nodes[dst]

        src_highlight = Circle(radius=0.18, color=DARK_BLUE).move_to(src_dot)
        dst_highlight = Circle(radius=0.18, color=DARK_BROWN).move_to(dst_dot)

        self.play(Create(src_highlight), Create(dst_highlight))
        self.wait(7.5)

        # --- Helper to find shortest path in adjacency ---
        def bfs_path(start, goal):
            from collections import deque
            queue = deque([[start]])
            visited = set([start])
            while queue:
                path = queue.popleft()
                node = path[-1]
                if node == goal:
                    return path
                for nei in adjacency[node]:
                    if nei not in visited:
                        visited.add(nei)
                        queue.append(path + [nei])
            return []

        # Get path before rewiring (you can store adjacency before rewiring)
        # For simplicity, rebuild original lattice adjacency
        lattice_adj = {i: set([(i+1)%N, (i-1)%N, (i+2)%N, (i-2)%N]) for i in range(N)}
        def lattice_bfs_path(start, goal):
            from collections import deque
            queue = deque([[start]])
            visited = set([start])
            while queue:
                path = queue.popleft()
                node = path[-1]
                if node == goal:
                    return path
                for nei in lattice_adj[node]:
                    if nei not in visited:
                        visited.add(nei)
                        queue.append(path + [nei])
            return []

        old_path = lattice_bfs_path(src, dst)
        new_path = bfs_path(src, dst)
        
        lattice_edge_map = {}
        for k, v in edge_map.items():
            # copy so later changes to the scene don't modify these
            lattice_edge_map[k] = v.copy().set_stroke(width=2).set_color(GREY_B)

        

        # Function to draw path lines
        def draw_path(path, color, use_current=True):
            """
                path: list of node indices
                color: color to draw with
                use_current: if True, use edge_map (post-rewiring, contains shortcuts).
                            if False, use lattice_edge_map (original lattice arcs).
            """
            lines = []
            source_map = edge_map if use_current else lattice_edge_map

            for i in range(len(path) - 1):
                a, b = path[i], path[i + 1]
                key = (min(a, b), max(a, b))

                if key in source_map:
                # use the existing arc for visual consistency
                    seg = source_map[key].copy()
                    seg.set_color(color)
                    seg.set_stroke(width=4)
                    # ensure it's drawn above node dots
                    seg.move_to(seg.get_center())  # no-op but safe
                    lines.append(seg)
                else:
                    # fallback to computed arc (same logic as arc_connection)
                    p1, p2 = nodes[a].get_center(), nodes[b].get_center()
                    center = np.array([0, 0, 0])
                    curvature = 0.8 if np.cross(p1 - center, p2 - center)[2] > 0 else -0.8
                    arc = ArcBetweenPoints(p1, p2, angle=curvature, color=color, stroke_width=4)
                    lines.append(arc)

            return VGroup(*lines)
        
        def make_hop_text(count, color=WHITE):
            text = Text(f"Hops: {count}", font_size=28, color=color)
            text.to_corner(DR).shift(UP * 0.3 + LEFT * 0.3)
            return text


        old_path_lines = draw_path(old_path, color=DARK_BLUE)
        new_path_lines = draw_path(new_path, color=DARK_BROWN)

        

        # Animate old (long) path
        old_hop_text = make_hop_text(len(old_path) - 1, color=DARK_BLUE)
        self.play(Create(old_path_lines), FadeIn(old_hop_text))
        self.wait(4.5)

        # Transition to new (shorter) path
        new_hop_text = make_hop_text(len(new_path) - 1, color=DARK_BROWN)
        self.play(FadeOut(old_path_lines), Transform(old_hop_text, new_hop_text))
        self.play(Create(new_path_lines))
        self.wait(4)

        self.play(FadeOut(new_path_lines), FadeOut(src_highlight), FadeOut(dst_highlight))
        self.wait(3)


        # info_text = Text(
        #     f"hehe | Rewire fraction = {rewire_fraction}",
        #     font_size=28,
        #     color=WHITE
        # ).to_corner(DOWN)
        # self.play(Write(info_text))

        self.wait(3)
