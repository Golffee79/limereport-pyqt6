"""Apply idempotent LimeReport singleton teardown fix to pinned vendored source."""
from pathlib import Path
import sys

path = Path(sys.argv[1])
source = path.read_text(encoding='utf-8')
old = '    static T& instance()\n'
new = '    static void destroyIfExists() { destroy(); }\n\n    static T& instance()\n'
old_destroy = '    static void destroy() { delete inst; }'
new_destroy = '    static void destroy() { T* old = inst; inst = nullptr; delete old; }'
if source.count(old) == 1 and source.count(old_destroy) == 1:
    path.write_text(source.replace(old, new, 1).replace(old_destroy, new_destroy, 1), encoding='utf-8')
elif source.count(new) == 1 and source.count(new_destroy) == 1:
    pass
else:
    sys.exit('Pinned LimeReport singleton source differs from expected context')
