# -*- coding: utf-8 -*-
"""Creator plugin for creating fbx.

It was made to pratice publish process.
"""
from openpype.hosts.houdini.api import plugin

import hou


class CreateFilmboxFBX(plugin.HoudiniCreator):
    """Filmbox FBX Driver"""
    identifier = "io.openpype.creators.houdini.filmboxfbx"
    label = "Filmbox FBX"
    family = "filmboxfbx"
    icon = "fa5s.cubes"

    # Overrides HoudiniCreator.create()
    def create(self, subset_name, instance_data, pre_create_data):
        # instance_data.pop("active", None)

        # set node type
        instance_data.update({"node_type": "filmboxfbx"})

        # set essential extra parameters
        instance = super(CreateFilmboxFBX, self).create(
            subset_name,
            instance_data,
            pre_create_data)

        # get the created node
        instance_node = hou.node(instance.get("instance_node"))

        # get output path
        output_path = hou.text.expandString(
            "$HIP/pyblish/{}.fbx".format(subset_name))

        # get selection
        selection = self.get_selection()

        # parms dictionary
        parms = {
            "startnode" : selection,
            "sopoutput": output_path
        }

        # set parms
        instance_node.setParms(parms)

        # Lock any parameters in this list
        to_lock = []
        self.lock_parameters(instance_node, to_lock)

    # Overrides HoudiniCreator.get_network_categories()
    def get_network_categories(self):
        return [
            hou.ropNodeTypeCategory(),
            hou.sopNodeTypeCategory()
        ]

    def get_selection(self):
        """Selection Logic.

        how self.selected_nodes should be processed to get
        the desirable node from selection.

        Returns:
            str : node path
        """

        selection = ""

        if self.selected_nodes:
            selected_node = self.selected_nodes[0]

            # Although Houdini allows ObjNode path on `startnode` for the
            # the ROP node we prefer it set to the SopNode path explicitly

            # Allow sop level paths (e.g. /obj/geo1/box1)
            if isinstance(selected_node, hou.SopNode):
                selection = selected_node.path()
                self.log.debug(
                    "Valid SopNode selection, 'Export' in filmboxfbx"
                    " will be set to '%s'."
                    % selected_node
                )

            # Allow object level paths to Geometry nodes (e.g. /obj/geo1)
            # but do not allow other object level nodes types like cameras, etc.
            elif isinstance(selected_node, hou.ObjNode) and \
                    selected_node.type().name() in ["geo"]:

                # get the output node with the minimum
                # 'outputidx' or the node with display flag
                sop_path = self.get_obj_output(selected_node)

                if sop_path:
                    selection = sop_path.path()
                    self.log.debug(
                        "Valid ObjNode selection, 'Export' in filmboxfbx "
                        "will be set to the child path '%s'."
                        % sop_path
                    )

            if not selection:
                self.log.debug(
                    "Selection isn't valid. 'Export' in filmboxfbx will be empty."
                )
        else:
            self.log.debug(
                "No Selection. 'Export' in filmboxfbx will be empty."
            )

        return selection

    def get_obj_output(self, obj_node):
        """Find output node with the smallest 'outputidx'
        or return tje node with the render flag instead.
        """

        outputs = obj_node.subnetOutputs()

        # if obj_node is empty
        if not outputs:
            return

        # if obj_node has one output child whether its
        # sop output node or a node with the render flag
        elif len(outputs) == 1:
            return outputs[0]

        # if there are more than one, then it have multiple ouput nodes
        # return the one with the minimum 'outputidx'
        else:
            return min(outputs,
                       key=lambda node: node.evalParm('outputidx'))
