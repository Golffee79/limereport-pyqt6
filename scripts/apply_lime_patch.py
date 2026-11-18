"""Idempotent, exact-context downstream fix for pinned LimeReport 1.7.23."""
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
source = path.read_text(encoding="utf-8")
old = """    if (groupHeader->reprintOnEachPage())
        m_reprintableBands.removeOne(groupHeader);
    foreach (BandDesignIntf* header, groupHeader->childrenByType(BandDesignIntf::GroupHeader)) {
"""
new = """    // Keep the group header reprintable while its footer is paginated.
    // Otherwise a footer pushed to the next page loses its route header.
    foreach (BandDesignIntf* header, groupHeader->childrenByType(BandDesignIntf::GroupHeader)) {
"""
old_footer = """        renderBand(footer, 0, StartNewPageAsNeeded);
    }
    closeDataGroup(groupHeader);
"""
new_footer = """        renderBand(footer, 0, StartNewPageAsNeeded);
    }
    // closeDataGroup removes this header after all footers have rendered.
    closeDataGroup(groupHeader);
"""
if source.count(old) == 1 and source.count(old_footer) == 1:
    path.write_text(source.replace(old, new, 1).replace(old_footer, new_footer, 1), encoding="utf-8")
elif source.count(new) == 1 and source.count(new_footer) == 1:
    pass  # Already patched (e.g. repeated CMake configuration).
else:
    sys.exit("Pinned LimeReport source differs from the expected patch context")
