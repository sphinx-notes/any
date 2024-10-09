# def run_objdesc(self, obj: Object) -> list[Node]:
#     descnode = addnodes.desc()
# 
#     # Generate signature node
#     title = self.schema.title_of(obj)
#     if title is None:
#         # Use non-generated object ID as replacement of title
#         idfield, objid = self.schema.identifier_of(obj)
#         title = objid if idfield is not None else None
#     if title is not None:
#         signode = addnodes.desc_signature(title, '')
#         signode += addnodes.desc_name(title, title)
#         descnode.append(signode)
#     else:
#         signode = None
# 
#     # Generate content node
#     contnode = addnodes.desc_content()
#     descnode.append(contnode)
#     self._setup_nodes(obj, descnode, signode, contnode)
#     return [descnode]

