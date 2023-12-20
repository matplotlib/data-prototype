from __future__ import annotations

from collections.abc import Iterable, Callable, Sequence
from collections import Counter
from dataclasses import dataclass
from enum import Enum, auto
import inspect
from functools import cached_property

from typing import Any


def evaluate_pipeline(nodes: Sequence[ConversionNode], input: dict[str, Any]):
    for node in nodes:
        input = node.evaluate(input)
    return input


def preview_pipeline(nodes: Sequence[ConversionNode], input: Iterable[str]):
    out = [tuple(input)]
    for node in nodes:
        out.append(node.preview_keys(out[-1]))
    return out


def simplify_pipeline(nodes: Sequence[ConversionNode], output_keys: Iterable[str]):
    out_nodes = []
    required_keys = set(output_keys)
    for node in reversed(nodes):
        print(node, required_keys)
        next_required = set()
        next_removed = set()
        for key in required_keys:
            effect, added_reqs = node.affects_key(key)
            print(key, effect, added_reqs)
            if effect == AffectsKey.CREATE:
                next_removed.update(key)
                next_required |= set(added_reqs)
                out_nodes.insert(0, node)
            elif effect == AffectsKey.MODIFY:
                next_required |= set(added_reqs)
                out_nodes.insert(0, node)
            elif effect == AffectsKey.REMOVE:
                raise ValueError(f"Required key {key!r} removed by node")
        required_keys |= next_required
        required_keys -= next_removed
    return out_nodes


class AffectsKey(Enum):
    CREATE = auto()
    MODIFY = auto()
    REMOVE = auto()
    IGNORE = auto()
    USE = auto()


@dataclass
class ConversionNode:
    required_keys: tuple[str, ...]
    output_keys: tuple[str, ...]

    def preview_keys(self, input_keys: Iterable[str]) -> tuple[str, ...]:
        if missing_keys := set(self.required_keys) - set(input_keys):
            raise ValueError(f"Missing keys: {missing_keys}")
        return tuple(sorted(set(input_keys) | set(self.output_keys)))

    def affects_key(self, key: str) -> tuple[AffectsKey, tuple[str, ...]]:
        inp = key in self.required_keys
        outp = key in self.output_keys
        if inp and outp:
            return AffectsKey.MODIFY, self.required_keys
        elif inp:
            return AffectsKey.USE, ()
        elif outp:
            return AffectsKey.CREATE, self.required_keys
        else:
            return AffectsKey.IGNORE, ()

    def evaluate(self, input: dict[str, Any]) -> dict[str, Any]:
        if missing_keys := set(self.output_keys) - set(input):
            raise ValueError(f"Missing keys: {missing_keys}")
        return input


@dataclass
class UnionConversionNode(ConversionNode):
    nodes: tuple[ConversionNode, ...]

    @classmethod
    def from_nodes(cls, *nodes: ConversionNode):
        required = tuple(set(k for n in nodes for k in n.required_keys))
        output = Counter(k for n in nodes for k in n.output_keys)
        if duplicate := {k for k, v in output.items() if v > 1}:
            raise ValueError(f"Duplicate keys from multiple input nodes: {duplicate}")
        return cls(required, tuple(output), nodes)

    def evaluate(self, input: dict[str, Any]) -> dict[str, Any]:
        return super().evaluate(
            {k: v for n in self.nodes for k, v in n.evaluate(input).items()}
        )


@dataclass
class RenameConversionNode(ConversionNode):
    mapping: dict[str, str]

    def affects_key(self, key: str) -> tuple[AffectsKey, tuple[str, ...]]:
        inp = key in self.mapping
        outp = key in self.mapping.values()
        if inp and outp:
            return AffectsKey.MODIFY, self.required_keys
        elif inp:
            return AffectsKey.REMOVE, self.required_keys
        elif outp:
            return AffectsKey.CREATE, self.required_keys
        else:
            return AffectsKey.IGNORE, ()

    @classmethod
    def from_mapping(cls, mapping: dict[str, str]):
        required = tuple(mapping)
        output = Counter(mapping.values())
        if duplicate := {k for k, v in output.items() if v > 1}:
            raise ValueError(f"Duplicate output keys in mapping: {duplicate}")
        return cls(required, tuple(output), mapping)

    def evaluate(self, input: dict[str, Any]) -> dict[str, Any]:
        return super().evaluate(
            {**input, **{out: input[inp] for (inp, out) in self.mapping.items()}}
        )


@dataclass
class FunctionConversionNode(ConversionNode):
    funcs: dict[str, Callable]

    @cached_property
    def _sigs(self):
        return {k: (f, inspect.signature(f)) for k, f in self.funcs.items()}

    @classmethod
    def from_funcs(cls, funcs: dict[str, Callable]):
        sigs = {k: inspect.signature(f) for k, f in funcs.items()}
        output = tuple(sigs)
        input = set()
        for v in sigs.values():
            input |= set(v.parameters.keys())
        input = tuple(input)
        return cls(input, output, funcs)

    def evaluate(self, input: dict[str, Any]) -> dict[str, Any]:
        return super().evaluate(
            {
                **input,
                **{
                    k: func(**{p: input[p] for p in sig.parameters})
                    for (k, (func, sig)) in self._sigs.items()
                },
            }
        )


@dataclass
class LimitKeysConversionNode(ConversionNode):
    keys: set[str]

    def affects_key(self, key: str) -> tuple[AffectsKey, tuple[str, ...]]:
        if key in self.keys:
            return AffectsKey.IGNORE, ()
        return AffectsKey.REMOVE, ()

    @classmethod
    def from_keys(cls, keys: Sequence[str]):
        return cls((), tuple(keys), keys=set(keys))

    def evaluate(self, input: dict[str, Any]) -> dict[str, Any]:
        return {k: v for k, v in input.items() if k in self.keys}
