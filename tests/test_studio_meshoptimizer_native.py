"""Compile the real pinned upstream geometry optimization subset; no GPU claim."""
import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1] / "third_party" / "meshoptimizer" / "src"


def test_real_meshoptimizer_cache_and_fetch(tmp_path):
    compiler = shutil.which("c++")
    if not compiler:
        if os.environ.get("GITHUB_ACTIONS") == "true":
            pytest.fail("C++ compiler required for meshoptimizer proof")
        pytest.skip("native C++ compiler unavailable; no native proof")
    source = tmp_path / "check.cpp"
    source.write_text(r"""
#include "meshoptimizer.h"
#include <algorithm>
#include <array>
#include <cassert>
#include <vector>
using Tri = std::array<unsigned int, 3>;
int main() {
    const unsigned int indices[] = {0,1,2, 4,5,6, 2,1,3, 6,5,7, 0,2,3};
    const size_t count = sizeof(indices)/sizeof(indices[0]);
    std::vector<unsigned int> result(count);
    meshopt_optimizeVertexCache(result.data(), indices, count, 8);
    auto triangles = [](const unsigned int* data, size_t n) {
        std::vector<Tri> t;
        for (size_t i=0; i<n; i+=3) t.push_back({data[i],data[i+1],data[i+2]});
        std::sort(t.begin(),t.end());
        return t;
    };
    assert(triangles(indices,count) == triangles(result.data(),count));
    const unsigned int vertices[] = {100,101,102,103,104,105,106,107};
    std::vector<unsigned int> remapped(8);
    auto before = result;
    size_t used = meshopt_optimizeVertexFetch(remapped.data(),result.data(),count,
                                               vertices,8,sizeof(unsigned int));
    assert(used == 8);
    for (size_t i=0; i<count; ++i) {
        assert(result[i] < used);
        assert(remapped[result[i]] == vertices[before[i]]);
    }
    return 0;
}
""")
    exe = tmp_path / "check"
    subprocess.run([compiler, "-std=c++11", "-O2", "-I", str(ROOT), str(source),
                    *(str(ROOT / name) for name in ("allocator.cpp", "vcacheoptimizer.cpp", "vfetchoptimizer.cpp")),
                    "-o", str(exe)], check=True, timeout=90)
    subprocess.run([str(exe)], check=True, timeout=15)
