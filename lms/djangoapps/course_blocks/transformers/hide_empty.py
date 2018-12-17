"""
Hide Empty Transformer implementation.
"""
from openedx.core.djangoapps.content.block_structure.transformer import (
    BlockStructureTransformer
)

from .utils import collect_merged_boolean_field


class HideEmptyTransformer(BlockStructureTransformer):
    """
    A transformer that removes any block from the course that could have
    children but doesn't.
    """
    WRITE_VERSION = 1
    READ_VERSION = 1

    @classmethod
    def name(cls):
        """
        Unique identifier for the transformer's class;
        same identifier used in setup.py.
        """
        return "hide_empty"

    @classmethod
    def collect(cls, block_structure):
        """
        Collects any information that's necessary to execute this
        transformer's transform method.
        """
        block_structure.request_xblock_fields('children', 'has_children')

    def transform(self, usage_info, block_structure):
        """
        By defining this method, FilteringTransformers can be run individually
        if desired. In normal operations, the filters returned from multiple
        transform_block_filters calls will be combined and used in a single
        tree traversal.
        """

        def filter(block_key):
            has_children = block_structure.get_xblock_field(block_key, 'has_children')
            children = block_structure.get_xblock_field(block_key, 'children')
            return has_children and not any(child in block_structure for child in children)

        for _ in block_structure.topological_traversal(
            filter_func=block_structure.create_removal_filter(filter)
        ):
            pass
