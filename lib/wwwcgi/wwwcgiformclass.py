""" Example of a module containing python class which can by supplied
to wwwcgi script to create of html form for changing this class' properties """

class wwwcgiformclass:
    def setprop1(self, value):
        self.__prop1 = value
    def getprop1(self, value):
        return self.__prop1

    def setprop2(self, value):
        self.__prop2 = value
    def getprop2(self, value):
        return self.__prop2
    
    def __init__(self):
        self.__prop1 = None
        self.__prop2 = None
        self.prop1 = property(self.getprop1, self.setprop1, None, 'Property 1')
        self.prop2 = property(self.getprop2, self.setprop2, None, 'Property 2')

    def getpropnames(self):
        prop = property()
        return [p for p in dir(self) if type(getattr(self, p)) == type(prop)]


def test():
    w = wwwcgiformclass()
    print w.getpropnames()
    print dir(property())
if __name__ == '__main__':
    test()