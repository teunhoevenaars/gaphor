"""Report differences in two Gaphor models.

This can be called as:
    python compare.py model1.gaphor model2.gaphor

This file is part of Gaphor.
"""

__all__ = ["Compare"]

import gaphor.storage
import gaphor.storage.parser
import gaphor.UML


class Compare:
    """This class makes it possible to compare two files.
    By default reports are printed to stdout in a diff-like syntax.
    """

    def __init__(self, filename1, filename2):
        self.filename1 = filename1
        self.filename2 = filename2

        self.elements1, self.factory1 = self.load(self.filename1)
        self.elements2, self.factory2 = self.load(self.filename2)

        self.show_id = True

    def out(self, msg):
        """Print a message generated by report().
        """
        print(msg)

    def report(self, factory, element, name=None, value=None, isref=False):
        """Report an element that has differences.
        The attribute show_id can be set to False to suppress element ids.
        A fancy diff message is send to method out(msg).
        """
        if factory is self.factory1:
            msg = "-"
        else:
            msg = "+"

        if isinstance(element, gaphor.storage.parser.canvas):
            msg += " <canvas>:"
        else:
            if self.show_id:
                msg += f" {element.id}"
            n = element.get("name")
            if n:
                msg += f" ({n})"
            if self.show_id or n:
                msg += ":"

        msg += " %s" % (
            isinstance(element, gaphor.storage.parser.canvas)
            and "Canvas"
            or element.type
        )

        if name:
            msg += f".{name}"
            if value:
                if isref:
                    if self.show_id:
                        msg += f" = {value}"
                    obj = factory.lookup(value)
                    if hasattr(obj, "name"):
                        msg += f" ({obj.name})"
                else:
                    msg += f" = {value}"

        self.out(msg)

    def load(self, filename):
        """Load the model file and create a factory.
        A tuple (elements, factory) is returned.
        """
        elements = gaphor.storage.parser.parse(filename)
        factory = gaphor.UML.ElementFactory()
        try:
            gaphor.storage.load_elements(elements, factory)
        except Exception as e:
            self.out(f"! File {filename} could not be loaded completely.")
            self.out("! Trying to diff on parsed elements only.")
            self.out(e)
        return elements, factory

    def elements_in_both_files(self):
        """Generator function that returns tuples (element1, element2) of
        elements that exist in both files (they have the same id).
        """
        vals = []
        for key1, val1 in list(self.elements1.items()):
            val2 = self.elements2.get(key1)
            if val2:
                yield (val1, val2)

    def check_missing_elements(self):
        """Report elements that exist in one factory, but not in the other.
        """
        keys1 = list(self.elements1.keys())
        keys2 = list(self.elements2.keys())
        for key in keys1:
            if key not in keys2:
                self.report(self.factory1, self.elements1[key])

        for key in keys2:
            if key not in keys1:
                self.report(self.factory2, self.elements2[key])

    def check_missing_references(self, element1, element2):
        """Report references to other elements that are present in one
        element and not in the other one.
        """
        keys1 = list(element1.references.keys())
        keys2 = list(element2.references.keys())
        for key in keys1:
            if key not in keys2:
                self.report(self.factory1, element1, key)

        for key in keys2:
            if key not in keys1:
                self.report(self.factory2, element2, key)

    def check_differences_references(self, element1, element2):
        keys1 = list(element1.references.keys())
        keys2 = list(element2.references.keys())
        for key in keys1:
            if key in keys2:
                val1 = element1.references.get(key)
                val2 = element2.references.get(key)
                try:
                    for val in val1:
                        if val not in val2:
                            self.report(self.factory1, element1, key, val, True)

                    for val in val2:
                        if val not in val1:
                            self.report(self.factory2, element2, key, val, True)
                except TypeError:
                    if val1 != val2:
                        self.report(self.factory1, element1, key, val1, True)
                        self.report(self.factory2, element2, key, val2, True)

    def check_missing_values(self, element1, element2):
        keys1 = list(element1.values.keys())
        keys2 = list(element2.values.keys())
        for key in keys1:
            if key not in keys2:
                self.report(self.factory1, element1, key)

        for key in keys2:
            if key not in keys1:
                self.report(self.factory2, element2, key)

    def check_differences_values(self, element1, element2):
        keys1 = list(element1.values.keys())
        keys2 = list(element2.values.keys())
        for key in keys1:
            if key in keys2:
                val1 = element1.values.get(key)
                val2 = element2.values.get(key)
                if val1 != val2:
                    self.report(self.factory1, element1, key, val1)
                    self.report(self.factory2, element2, key, val2)

    def compare(self):
        """Start the comparison of the files provided to the constructor.
        """
        self.check_missing_elements()

        for element1, element2 in self.elements_in_both_files():
            self.check_missing_references(element1, element2)
            self.check_differences_references(element1, element2)
            self.check_missing_values(element1, element2)
            self.check_differences_values(element1, element2)


if __name__ == "__main__":
    import sys

    usage = f"usage: {sys.argv[0]} [-v][-h|--help] old_model new_model"
    files = []
    show_id = False

    # Parse command line arguments:
    for arg in sys.argv[1:]:
        if arg.startswith("-"):
            if arg == "-v":
                show_id = True
            elif arg in ("-h", "--help"):
                print(usage)
                sys.exit(0)
            else:
                print(f'{sys.argv[0]}: invalid option "{arg}".')
                print(usage)
                sys.exit(1)
        else:
            files.append(arg)

    if len(files) != 2:
        print(usage)
        sys.exit(1)

    c = Compare(files[0], files[1])
    c.show_id = show_id
    c.compare()
