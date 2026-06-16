from __future__ import annotations

import heapq
from math import inf
from typing import Any


class drone_algo:

    def __init__(self, parser_instance: Any):
        self.parser_instance = parser_instance
        self._in_transit: dict[str, tuple[str, str]] = {}
        self._dist_to_goal: dict[str, float] = {}

        self.turn_units: int = 0
        self._rebuild_routing_table()

    def _rebuild_routing_table(self) -> None:

        vm = self.parser_instance.vars
        goals = [z.name for z in vm.values() if getattr(
            z, "hub_kind", None
            ) == "end"]
        dist: dict[str, float] = {name: inf for name in vm}
        pq: list[tuple[float, str]] = []
        for g in goals:
            dist[g] = 0.0
            heapq.heappush(pq, (0.0, g))

        pred: dict[str, list[str]] = {n: [] for n in vm}
        for zname, z in vm.items():
            for t in getattr(z, "connections", []) or []:
                if t in pred:
                    pred[t].append(zname)

        while pq:
            d, u = heapq.heappop(pq)
            if d > dist[u]:
                continue
            for v in pred.get(u, []):
                w = self._move_cost_into_inst(u)
                if w >= inf:
                    continue
                nd = d + w
                if nd < dist[v]:
                    dist[v] = nd
                    heapq.heappush(pq, (nd, v))
        self._dist_to_goal = dist

    def _move_cost_into_inst(self, dest_zone_name: str) -> float:
        vm = self.parser_instance.vars
        z = vm.get(dest_zone_name)
        if z is None:
            return inf
        if getattr(z, "zone_type", "normal") in ("blocked", "no_fly"):
            return inf
        if z.zone_type == "restricted":
            return 2.0
        return 1.0

    def dist_to_goal(self, zone_name: str | None) -> float:
        if not zone_name:
            return inf
        return self._dist_to_goal.get(zone_name, inf)

    def begin_turn(self) -> None:

        vm = self.parser_instance.vars
        for did, (src, dst) in list(self._in_transit.items()):
            zd = vm.get(dst)
            if zd is None:
                del self._in_transit[did]
                continue
            if len(zd.drones) >= zd.max_drones:
                continue
            zd.drones.append(did)
            zd.pending_incoming = max(0, getattr(
                zd, "pending_incoming", 0
                ) - 1)
            self.turn_units += 1
            del self._in_transit[did]

    def in_transit(self, drone_id: str) -> tuple[str, str] | None:
        return self._in_transit.get(drone_id)

    def check_next_move(self, drone_id, current_zone, next_zone):
        if current_zone.zone_type == "no_fly":
            print(f"Drone {drone_id} cannot move from {current_zone.name} "
                  f"to {next_zone.name}: current zone is no-fly")
            return False
        if next_zone.zone_type == "no_fly":
            print(f"Drone {drone_id} cannot move from {current_zone.name} "
                  f"to {next_zone.name}: next zone is no-fly")
            return False
        if next_zone.zone_type == "blocked":
            print(f"Drone {drone_id} cannot move from {current_zone.name} "
                  f"to {next_zone.name}: next zone is blocked")
            return False
        occ = len(next_zone.drones) + getattr(next_zone, "pending_incoming", 0)
        if occ >= next_zone.max_drones:
            print(
                f"Drone {drone_id} cannot move from {current_zone.name} "
                f"to {next_zone.name}: next zone is at max capacity"
            )
            return False
        return True

    def _is_zone_traversable(self, current_zone, next_zone) -> bool:
        if current_zone.zone_type == "no_fly":
            return False
        if next_zone.zone_type in ("no_fly", "blocked"):
            return False
        return True

    def move_drone(self, drone_id, current_zone_name, next_zone_name):
        if (
            current_zone_name not in self.parser_instance.vars
        ) or next_zone_name not in self.parser_instance.vars:
            print("One or both zones not found")
            return False

        current_zone = self.parser_instance.vars[current_zone_name]
        next_zone = self.parser_instance.vars[next_zone_name]
        if self.check_next_move(drone_id, current_zone, next_zone) is False:
            return False

        if hasattr(current_zone, "drones") and drone_id in current_zone.drones:
            swaped_drone = current_zone.drones.pop(
                current_zone.drones.index(drone_id)
                )
            next_zone.drones.append(swaped_drone)
            print(f"Drone {drone_id} moved from {current_zone.name} "
                  f"to {next_zone.name}")
            return True
        else:
            print(f"Drone {drone_id} not found "
                  f"in current zone {current_zone.name}")
            return False

    def get_drone_location(self, drone_id):
        for zone in self.parser_instance.vars.values():
            if hasattr(zone, "drones") and drone_id in zone.drones:
                print(zone.name)
                return zone.name
        print(f"Drone {drone_id} not found")
        return None

    def get_possible_moves(
        self, drone_id, current_zone_name, *, consider_capacity: bool = True
    ) -> list[str]:
        if current_zone_name not in self.parser_instance.vars:
            print("Current zone not found")
            return []

        current_zone = self.parser_instance.vars[current_zone_name]
        possible_moves = []

        for next_zone_name in getattr(current_zone, "connections", []) or []:
            if next_zone_name in self.parser_instance.vars.keys():
                next_zone = self.parser_instance.vars[next_zone_name]
                if consider_capacity:
                    if self.check_next_move(drone_id, current_zone, next_zone):
                        possible_moves.append(next_zone_name)
                elif self._is_zone_traversable(current_zone, next_zone):
                    possible_moves.append(next_zone_name)
        return possible_moves

    def _preference_rank(self, move_name: str) -> int:
        z = self.parser_instance.vars.get(move_name)
        if z is None:
            return 0
        if getattr(z, "hub_kind", None) == "end":
            return 4
        zt = getattr(z, "zone_type", "normal") or "normal"
        if zt == "priority":
            return 3
        if zt == "normal":
            return 2
        if zt == "restricted":
            return 1
        return 2

    def _occupancy_pressure(self, zone_name: str) -> int:
        z = self.parser_instance.vars.get(zone_name)
        if z is None:
            return 9999
        return len(z.drones) + getattr(z, "pending_incoming", 0)

    def validate_possible_moves(
        self, possible_moves: list[str], current_zone_name: str
    ) -> str | None:

        if not possible_moves:
            return None
        feasible = [m for m in possible_moves if self.dist_to_goal(m) < inf]
        if not feasible:
            return None
        best: str | None = None
        best_key: tuple | None = None
        for m in feasible:
            dm = self.dist_to_goal(m)
            pref = self._preference_rank(m)
            load = self._occupancy_pressure(m)
            tie = m
            key = (dm, -pref, load, tie)
            if best_key is None or key < best_key:
                best_key = key
                best = m
        return best

    def current_zone_for_drone(self, drone_id):
        if drone_id in self._in_transit:
            return None
        for zone in self.parser_instance.vars.values():
            if hasattr(zone, "drones") and drone_id in zone.drones:
                return zone.name
        return None

    def transit_visual_anchor(self, drone_id: str) -> tuple[str, str] | None:
        """If in restricted transit, (src, dst) for drawing."""
        return self._in_transit.get(drone_id)

    def all_drones_at_goal(self):
        if self._in_transit:
            return False
        for i in range(self.parser_instance.nb_drones):
            loc = self.current_zone_for_drone(f"drone{i}")
            if loc is None:
                return False
            z = self.parser_instance.vars[loc]
            if getattr(z, "hub_kind", None) != "end":
                return False
        return True

    def _link_cap(self, src_name: str, dst_name: str) -> int | None:
        zs = self.parser_instance.vars.get(src_name)
        if zs is None:
            return None
        caps = getattr(zs, "link_capacity", {}) or {}
        if dst_name not in caps:
            return None
        return int(caps[dst_name])

    def apply_resolved_moves(self, proposals: dict[str, tuple[Any, Any]]):

        vm = self.parser_instance.vars
        end = {k: list(getattr(z, "drones", [])) for k, z in vm.items()}
        nb = self.parser_instance.nb_drones
        edge_use: dict[tuple[str, str], int] = {}

        order = list(range(nb))
        order.sort(
            key=lambda i: (
                self.dist_to_goal(
                    (proposals.get(f"drone{i}") or (None, None))[0],
                ),
                i,
            )
        )

        for i in order:
            did = f"drone{i}"
            if did not in proposals:
                continue
            src, dst = proposals[did]
            if src is None or dst is None or src == dst:
                continue
            if src not in end or did not in end[src]:
                continue
            cap_e = self._link_cap(src, dst)
            if cap_e is not None and edge_use.get((src, dst), 0) >= cap_e:
                continue

            zd = vm[dst]
            tent = {k: list(v) for k, v in end.items()}
            tent[src].remove(did)

            restricted = getattr(zd, "zone_type", "normal") == "restricted"

            if restricted:
                pend = getattr(vm[dst], "pending_incoming", 0)
                occ = len(tent[dst]) + pend
                if occ >= zd.max_drones:
                    continue
                zone_ok = True
                for zk, z in vm.items():
                    if len(tent[zk]) > z.max_drones:
                        zone_ok = False
                        break
                if not zone_ok:
                    continue
                vm[dst].pending_incoming = pend + 1
                self._in_transit[did] = (src, dst)
                end = tent
                if cap_e is not None:
                    edge_use[(src, dst)] = edge_use.get((src, dst), 0) + 1
                self.turn_units += 1
                print(f"Drone {did} restricted-transit {src} -> {dst} "
                      f"(arrives next turn)")
                continue

            tent[dst].append(did)
            valid = True
            for zk, z in vm.items():
                if len(tent[zk]) > z.max_drones:
                    valid = False
                    break
            if valid:
                end = tent
                if cap_e is not None:
                    edge_use[(src, dst)] = edge_use.get((src, dst), 0) + 1
                self.turn_units += 1
                print(f"Drone {did} moved from {src} to {dst}")

        for k, z in vm.items():
            z.drones = end[k]

    def decide_next_move(self, drone_id, current_zone_name, quiet=False):

        possible_moves = self.get_possible_moves(
            drone_id, current_zone_name, consider_capacity=False
            )
        if not quiet:
            print(f"Possible moves: {possible_moves}")

        if not possible_moves:
            if not quiet:
                print(f"No possible moves for drone {drone_id} "
                      f"from {current_zone_name}")
            return None

        best_move = self.validate_possible_moves(
            possible_moves, current_zone_name
            )
        if not quiet:
            print(f"check best move: {best_move}")
        return best_move
