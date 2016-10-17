'''
Teach django webpack loader to accept webpack files with hash query in path.
'''

import re
from webpack_loader import __version__
from webpack_loader.loader import WebpackLoader

if '0.3.1' <= __version__ <= '0.3.3':
    def patch__load_assets(old__load_assets):
        def new__load_assets(self):
            assets = old__load_assets(self)
            for bundle_name, bundle in assets.get('chunks', {}).items():
                for chunk in (bundle or []):
                    for field in ('name', 'path'):
                        chunk[field] = re.sub(r'\?[^/]+$', '', chunk[field])
            return assets
        return new__load_assets

    WebpackLoader._load_assets = patch__load_assets(WebpackLoader._load_assets)
