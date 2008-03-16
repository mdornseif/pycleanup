from distutils.core import setup

setup(
   name="2to3",
   packages=['lib2to3','lib2to3.fixes','pgen2'],
   package_data={'lib2to3':['Grammar.txt','PatternGrammar.txt']},
   scripts=["2to3"]
)
