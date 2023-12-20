from __future__ import annotations

from collections.abc import Iterable, Callable, Sequence
from collections import Counter
from dataclasses import dataclass
import inspect
from functools import cached_property

from typing import Any


def evaluate_pipeline(
    nodes: Sequence[ConversionNode],
    input: dict[str, Any],
    delayed_converters: dict[str, Callable] | None = None,
):
    for node in nodes:
        if isinstance(node, Callable):
            k = list(inspect.signature(node).parameters.keys())[0]
            node = FunctionConversionNode.from_funcs({k: node})
        if isinstance(node, DelayedConversionNode):
            input = node.evaluate(input, delayed_converters)
        else:
            input = node.evaluate(input)
    return input


@dataclass
class ConversionNode:
    required_keys: tuple[str, ...]
    output_keys: tuple[str, ...]
    trim_keys: bool

    def preview_keys(self, input_keys: Iterable[str]) -> tuple[str, ...]:
        if missing_keys := set(self.required_keys) - set(input_keys):
            raise ValueError(f"Missing keys: {missing_keys}")
        if self.trim_keys:
            return tuple(sorted(set(self.output_keys)))
        return tuple(sorted(set(input_keys) | set(self.output_keys)))

    def evaluate(self, input: dict[str, Any]) -> dict[str, Any]:
        if self.trim_keys:
            return {k: input[k] for k in self.output_keys}
        else:
            if missing_keys := set(self.output_keys) - set(input):
                raise ValueError(f"Missing keys: {missing_keys}")
            return input


@dataclass
class UnionConversionNode(ConversionNode):
    nodes: tuple[ConversionNode, ...]

    @classmethod
    def from_nodes(cls, *nodes: ConversionNode, trim_keys=False):
        required = tuple(set(k for n in nodes for k in n.required_keys))
        output = Counter(k for n in nodes for k in n.output_keys)
        if duplicate := {k for k, v in output.items() if v > 1}:
            raise ValueError(f"Duplicate keys from multiple input nodes: {duplicate}")
        return cls(required, tuple(output), trim_keys, nodes)

    def evaluate(self, input: dict[str, Any]) -> dict[str, Any]:
        return super().evaluate(
            {k: v for n in self.nodes for k, v in n.evaluate(input).items()}
        )


@dataclass
class RenameConversionNode(ConversionNode):
    mapping: dict[str, str]

    @classmethod
    def from_mapping(cls, mapping: dict[str, str], trim_keys=False):
        required = tuple(mapping)
        output = Counter(mapping.values())
        if duplicate := {k for k, v in output.items() if v > 1}:
            raise ValueError(f"Duplicate output keys in mapping: {duplicate}")
        return cls(required, tuple(output), trim_keys, mapping)

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
    def from_funcs(cls, funcs: dict[str, Callable], trim_keys=False):
        sigs = {k: inspect.signature(f) for k, f in funcs.items()}
        output = tuple(sigs)
        input = []
        for v in sigs.values():
            input.extend(v.parameters.keys())
        input = tuple(set(input))
        return cls(input, output, trim_keys, funcs)

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

    @classmethod
    def from_keys(cls, keys: Sequence[str]):
        return cls((), tuple(keys), trim_keys=True, keys=set(keys))

    def evaluate(self, input: dict[str, Any]) -> dict[str, Any]:
        return {k: v for k, v in input.items() if k in self.keys}


@dataclass
class DelayedConversionNode(ConversionNode):
    converter_key: str

    @classmethod
    def from_keys(cls, keys: Sequence[str], converter_key: str):
        return cls(
            tuple(keys), tuple(keys), trim_keys=False, converter_key=converter_key
        )

    def evaluate(
        self, input: dict[str, Any], converters: dict[str, Callable] | None = None
    ) -> dict[str, Any]:
        return super().evaluate(
            {
                **input,
                **{
                    k: converters[self.converter_key](input[k])
                    for k in self.required_keys
                },
            }
        )
