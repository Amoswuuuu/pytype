"""Tests of builtins (in pytd/builtins/__builtins__.pytd).

File 1/3. Split into parts to enable better test parallelism.
"""

import unittest
from pytype.tests import test_inference


class BuiltinTests(test_inference.InferenceTest):
  """Tests for builtin methods and classes."""

  def testRepr1(self):
    ty = self.Infer("""
      def t_testRepr1(x):
        return repr(x)
      t_testRepr1(4)
    """, deep=False, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      def t_testRepr1(x: int) -> str
    """)

  def testRepr2(self):
    ty = self.Infer("""
      def t_testRepr2(x):
        return repr(x)
      t_testRepr2(4)
      t_testRepr2(1.234)
      t_testRepr2('abc')
    """, deep=False, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      def t_testRepr2(x: float or int or str) -> str
    """)

  def testRepr3(self):
    ty = self.Infer("""
      def t_testRepr3(x):
        return repr(x)
      t_testRepr3(__any_object__())
    """, deep=False, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      def t_testRepr3(x) -> str
    """)

  def testEvalSolve(self):
    ty = self.Infer("""
      def t_testEval(x):
        return eval(x)
      t_testEval(4)
    """, deep=False, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      def t_testEval(x: int) -> ?
    """)

  def testIsinstance1(self):
    ty = self.Infer("""
      def t_testIsinstance1(x):
        # TODO: if isinstance(x, int): return "abc" else: return None
        return isinstance(x, int)
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      def t_testIsinstance1(x: object) -> bool
    """)

  @unittest.skip("Broken - needs more sophisticated booleans")
  def testIsinstance2(self):
    ty = self.Infer("""
      def t_testIsinstance2(x):
        assert isinstance(x, int)
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      # currently does (x: object)
      def t_testIsinstance2(x: int) -> NoneType
    """)

  def testPow1(self):
    ty = self.Infer("""
      def t_testPow1():
        # pow(int, int) returns int, or float if the exponent is negative.
        # Hence, it's a handy function for testing UnionType returns.
        return pow(1, -2)
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      def t_testPow1() -> float or int
    """)

  def testPow2(self):
    ty = self.Infer("""
      def t_testPow2(x, y):
        # pow(int, int) returns int, or float if the exponent is negative.
        # Hence, it's a handy function for testing UnionType returns.
        return pow(x, y)
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      def t_testPow2(x: complex or float or int, y: complex or float or int) -> complex or float or int
    """)

  def testMax1(self):
    ty = self.Infer("""
      def t_testMax1():
        # max is a parameterized function
        return max(1, 2)
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      def t_testMax1() -> int
      """)

  def testMax2(self):
    ty = self.Infer("""
      def t_testMax2(x, y):
        # max is a parameterized function
        return max(x, y)
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      def t_testMax2(x: object, y: object) -> ?
      """)

  def testZip(self):
    ty = self.Infer("""
      a = zip("foo", u"bar")
      b = zip(())
      c = zip((1, 2j))
      d = zip((1, 2, 3), ())
      e = zip((), (1, 2, 3))
      f = zip((1j, 2j), (1, 2))
      assert zip([], [], [])
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      from typing import List, Tuple, Union
      a = ...  # type: List[Tuple[str, unicode]]
      b = ...  # type: List[nothing]
      c = ...  # type: List[Tuple[Union[int, complex]]]
      d = ...  # type: List[nothing]
      e = ...  # type: List[nothing]
      f = ...  # type: List[Tuple[complex, int]]
      """)

  def testDict(self):
    ty = self.Infer("""
      def t_testDict():
        d = {}
        d['a'] = 3
        d[3j] = 1.0
        return _i1_(_i2_(d).values())[0]
      def _i1_(x):
        return x
      def _i2_(x):
        return x
      t_testDict()
    """, deep=False, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      from typing import Dict, List
      def t_testDict() -> float or int
      # _i1_, _i2_ capture the more precise definitions of the ~dict, ~list
      # TODO(kramm): The float/int split happens because
      # InterpreterFunction.get_call_combinations uses deep_product_dict(). Do
      # we want the output in this form?
      def _i1_(x: List[float]) -> List[float]
      def _i1_(x: List[int]) -> List[int]
      def _i2_(x: dict[complex or str, float or int]) -> Dict[complex or str, float or int]
    """)

  def testDictDefaults(self):
    ty = self.Infer("""
    def t_testDictDefaults(x):
      d = {}
      res = d.setdefault(x, str(x))
      _i_(d)
      return res
    def _i_(x):
      return x
    t_testDictDefaults(3)
    """, deep=False, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      def t_testDictDefaults(x: int) -> str
      # _i_ captures the more precise definition of the dict
      def _i_(x: dict[int, str]) -> dict[int, str]
    """)

  def testDictGet(self):
    ty = self.Infer("""
      def f():
        mydict = {"42": 42}
        return mydict.get("42")
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      def f() -> int or NoneType
    """)

  def testDictGetOrDefault(self):
    ty = self.Infer("""
      def f():
        mydict = {"42": 42}
        return mydict.get("42", False)
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      def f() -> int
    """)

  def testListInit0(self):
    ty = self.Infer("""
    def t_testListInit0(x):
      return list(x)
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      from typing import Iterable
      def t_testListInit0(x: Iterable) -> list
    """)

  def testListInit1(self):
    ty = self.Infer("""
    def t_testListInit1(x, y):
      return x + [y]
    """, deep=True, solve_unknowns=True, show_library_calls=True)
    self.assertTypesMatchPytd(ty, """
      from typing import List, MutableSequence, Union
      def t_testListInit1(x: List[object] or MutableSequence[object], y) -> list or MutableSequence
    """)

  def testListInit2(self):
    ty = self.Infer("""
    def t_testListInit2(x, i):
      return x[i]
    z = __any_object__
    t_testListInit2(__any_object__, z)
    print z + 1
    """, deep=False, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      z = ...  # type: complex or float or int

      def t_testListInit2(x: object, i: complex or float or int) -> ?
    """)

  def testListInit3(self):
    ty = self.Infer("""
    def t_testListInit3(x, i):
      return x[i]
    t_testListInit3([1,2,3,'abc'], 0)
    """, deep=False, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      from typing import List
      def t_testListInit3(x: List[int or str, ...], i: int) -> int or str
    """)

  def testListInit4(self):
    # TODO(kramm): This test takes over six seconds
    ty = self.Infer("""
    def t_testListInit4(x):
      return _i_(list(x))[0]
    def _i_(x):
      return x
    t_testListInit4(__any_object__)
    """, deep=False, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      from typing import Iterable
      def t_testListInit4(x: Iterable) -> ?
      def _i_(x: list) -> list
    """)

  def testAbsInt(self):
    ty = self.Infer("""
      def t_testAbsInt(x):
        return abs(x)
      t_testAbsInt(1)
    """, deep=False, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      def t_testAbsInt(x: int) -> int
  """)

  def testAbs(self):
    ty = self.Infer("""
      def t_testAbs(x):
        return abs(x)
      t_testAbs(__any_object__)
    """, deep=False, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      from typing import SupportsAbs
      # Since SupportsAbs.__abs__ returns a type parameter, the return type
      # of abs(...) can be anything.
      def t_testAbs(x: SupportsAbs[object] or complex or float or int) -> ?
    """)

  def testCmp(self):
    ty = self.Infer("""
      def t_testCmp(x, y):
        return cmp(x, y)
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
    def t_testCmp(x, y) -> int
    """)

  def testCmpMulti(self):
    ty = self.Infer("""
      def t_testCmpMulti(x, y):
        return cmp(x, y)
      t_testCmpMulti(1, 2)
      t_testCmpMulti(1, 2.0)
      t_testCmpMulti(1.0, 2)
    """, deep=False, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      def t_testCmpMulti(x: float or int, y: int) -> int
      def t_testCmpMulti(x: int, y: float) -> int
    """)

  def testCmpStr(self):
    ty = self.Infer("""
      def t_testCmpStr(x, y):
        return cmp(x, y)
      t_testCmpStr("abc", "def")
    """, deep=False, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      def t_testCmpStr(x: str, y: str) -> int
    """)

  def testCmpStr2(self):
    ty = self.Infer("""
      def t_testCmpStr2(x, y):
        return cmp(x, y)
      t_testCmpStr2("abc", __any_object__)
    """, deep=False, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      def t_testCmpStr2(x: str, y) -> int
    """)

  def testTuple(self):
    self.Infer("""
      def f(x):
        return x
      def g(args):
        f(*tuple(args))
    """, deep=True, solve_unknowns=False, show_library_calls=True)

  def testTuple2(self):
    ty = self.Infer("""
      def f(x, y):
        return y
      def g():
        args = (4, )
        return f(3, *args)
      g()
    """, deep=True, solve_unknowns=False)
    self.assertTypesMatchPytd(ty, """
      from typing import Any, TypeVar
      _T1 = TypeVar("_T1")
      def f(x, y: _T1) -> _T1: ...
      def g() -> int: ...
    """)

  def testOpen(self):
    ty = self.Infer("""
      def f(x):
        with open(x, "r") as fi:
          return fi.read()
      """, deep=True, solve_unknowns=True, show_library_calls=True)
    self.assertTypesMatchPytd(ty, """
      def f(x: str or buffer or unicode) -> str
    """)

  def testSignal(self):
    ty = self.Infer("""
      import signal
      def f():
        signal.signal(signal.SIGALRM, 0)
    """, deep=True, solve_unknowns=True, show_library_calls=True)
    self.assertTypesMatchPytd(ty, """
      signal = ...  # type: module

      def f() -> NoneType
    """)

  def testSysArgv(self):
    ty = self.Infer("""
      import sys
      def args():
        return ' '.join(sys.argv)
      args()
    """, deep=False, solve_unknowns=False, show_library_calls=True)
    self.assertTypesMatchPytd(ty, """
      sys = ...  # type: module
      def args() -> str
    """)

  def testSetattr(self):
    ty = self.Infer("""
      class Foo(object):
        def __init__(self, x):
          for attr in x.__dict__:
            setattr(self, attr, getattr(x, attr))
    """, deep=True, solve_unknowns=False)
    self.assertTypesMatchPytd(ty, """
      class Foo(object):
        def __init__(self, x) -> NoneType
    """)

  def testMap1(self):
    ty = self.Infer("""
      def f(input_string, sub):
        return ''.join(map(lambda ch: ch, input_string))
    """, deep=True, solve_unknowns=True)
    self.assertOnlyHasReturnType(
        ty.Lookup("f"), self.strorunicode)

  def testMap2(self):
    ty = self.Infer("""
      class Foo(object):
        pass

      def f():
        return map(lambda x: x, [Foo()])
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      class Foo(object):
        pass

      def f() -> list
    """)

  def testArraySmoke(self):
    ty = self.Infer("""
      import array
      class Foo(object):
        def __init__(self):
          array.array('i')
    """, deep=True, solve_unknowns=False)
    ty.Lookup("Foo")  # smoke test

  def testArray(self):
    ty = self.Infer("""
      import array
      class Foo(object):
        def __init__(self):
          self.bar = array.array('i', [1, 2, 3])
    """, deep=True, solve_unknowns=False)
    self.assertTypesMatchPytd(ty, """
      array = ...  # type: module
      class Foo(object):
        bar = ...  # type: array.array[int]
    """)

  def testInheritFromBuiltin(self):
    ty = self.Infer("""
      class Foo(list):
        pass
    """, deep=True, solve_unknowns=False)
    self.assertTypesMatchPytd(ty, """
      class Foo(list):
        pass
    """)

  def testOsPath(self):
    ty = self.Infer("""
      import os
      class Foo(object):
        bar = os.path.join('hello', 'world')
    """, deep=True, solve_unknowns=True)
    ty.Lookup("Foo")  # smoke test

  def testIsInstance(self):
    ty = self.Infer("""
      class Bar(object):
        def foo(self):
          return isinstance(self, Baz)

      class Baz(Bar):
        pass
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
    class Bar(object):
      def foo(self) -> bool

    class Baz(Bar):
      pass
    """)

  def testTime(self):
    ty = self.Infer("""
      import time
      def f(x):
        if x:
          return time.mktime(time.struct_time((1, 2, 3, 4, 5, 6, 7, 8, 9)))
        else:
          return 3j
    """, deep=True, solve_unknowns=False)
    self.assertTypesMatchPytd(ty, """
      time = ...  # type: module

      def f(x) -> complex or float
    """)

  def testDivMod(self):
    ty = self.Infer("""
      def seed(self, a=None):
        a = long(0)
        divmod(a, 30268)
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      def seed(self, a=...) -> NoneType
    """)

  def testDivMod2(self):
    ty = self.Infer("""
      def seed(self, a=None):
        if a is None:
          a = int(16)
        return divmod(a, 30268)
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      from typing import Tuple, Union
      def seed(self, a: Union[complex, float, int] = ...) -> Tuple[int or float or complex, ...]
    """)

  def testDivMod3(self):
    ty = self.Infer("""
      def seed(self, a=None):
        if a is None:
          a = long(16)
        return divmod(a, 30268)
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      from typing import Tuple, Union
      def seed(self, a: Union[complex, float, int] = ...) -> Tuple[int or float or complex, ...]
    """)

  def testOsOpen(self):
    ty = self.Infer("""
      import os
      def f():
        return open("/dev/null")
      def g():
        return os.open("/dev/null", os.O_RDONLY, 0777)
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      os = ...  # type: module

      def f() -> file
      def g() -> int
    """)

  def testJoin(self):
    ty = self.Infer("""
      def f(elements):
        return ",".join(t for t in elements)
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      def f(elements) -> str
    """)

  def testVersionInfo(self):
    ty = self.Infer("""
      import sys
      def f():
        return 'py%d' % sys.version_info[0]
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      sys = ...  # type: module
      def f() -> str
    """)

  def testInheritFromNamedTuple(self):
    ty = self.Infer("""
      import collections

      class Foo(
          collections.namedtuple('_Foo', 'x y z')):
        pass
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      collections = ...  # type: module

      class Foo(?):
        pass
    """)

  def testStoreAndLoadFromNamedTuple(self):
    ty = self.Infer("""
      import collections
      t = collections.namedtuple('t', ['x', 'y', 'z'])
      t.x = 3
      t.y = "foo"
      t.z = 1j
      x = t.x
      y = t.y
      z = t.z
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
    from typing import Any, Callable, Iterable, Tuple
    collections = ...  # type: module
    x = ...  # type: int
    y = ...  # type: str
    z = ...  # type: complex

    class t(tuple):
        __dict__ = ...  # type: collections.OrderedDict[str, Any]
        __slots__ = ...  # type: Tuple[nothing]
        _fields = ...  # type: Tuple[str, str, str]
        x = ...  # type: Any
        y = ...  # type: Any
        z = ...  # type: Any
        def __getnewargs__(self) -> Tuple[Any, Any, Any]: ...
        def __getstate__(self) -> None: ...
        def __new__(cls, x, y, z) -> t: ...
        def _asdict(self) -> collections.OrderedDict[str, Any]: ...
        @classmethod
        def _make(cls, iterable: Iterable, new = ..., len: Callable[[Iterable], int] = ...) -> t: ...
        def _replace(self, **kwds) -> t: ...
    """)

  def testTypeEquals(self):
    ty = self.Infer("""
      def f(n):
        return type(n) == type(0)
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      def f(n) -> bool
    """)

  def testTypeEquals2(self):
    ty = self.Infer("""
      import types
      def f(num):
        return type(num) == types.IntType
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      types = ...  # type: module
      def f(num) -> bool
    """)

  def testDateTime(self):
    ty = self.Infer("""
      import datetime

      def f(date):
        return date.ctime()
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      datetime = ...  # type: module
      def f(date: datetime.datetime or datetime.date) -> str
  """)

  def testFromUTC(self):
    ty = self.Infer("""
      import datetime

      def f(tz):
        tz.fromutc(datetime.datetime(1929, 10, 29))
    """, deep=True, solve_unknowns=True)
    self.assertTypesMatchPytd(ty, """
      datetime = ...  # type: module
      def f(tz: datetime.tzinfo) -> NoneType
  """)


if __name__ == "__main__":
  test_inference.main()
