
from docutils import nodes
from sphinx.util import logging
from sphinx import addnodes
from sphinx.util.docutils import SphinxDirective

logger = logging.getLogger(__name__)

class ObjDescDirective(SphinxDirective):
    def run(self) -> list[nodes.Node]:
        domainname, objtype = self.name.split(':', 1)
        domain = self.env.get_domain(domainname)

        descnode = addnodes.desc()
        descnode['domain'] = domain.name
        # 'desctype' is a backwards compatible attribute
        descnode['objtype'] = descnode['desctype'] = objtype
        descnode['classes'].append(domain.name)

        # Generate signature node.
        if self.arguments:
            title = self.arguments[0]
            signode = addnodes.desc_signature(title, '')
            signode += addnodes.desc_name(title, title)
            descnode += signode

            # TODO: anchor

        # Generate content node.
        contnode = addnodes.desc_content()
        if self.has_content:
            contnode += self.parse_content_to_nodes()
            descnode += contnode

        return [descnode]

