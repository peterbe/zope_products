import Recipe
"""RecipeProduct"""


def initialize(context):
    """ Initialize product """
    try:
        
        context.registerClass(
            Recipe.RecipeCollection,
            constructors = (
                # This is called when
                Recipe.manage_addRecipeCollectionForm,
                # someone adds the product
                Recipe.manage_addRecipeCollection
                ),
            icon = "www/collection.gif"
            )
        
        context.registerClass(
            Recipe.RecipeAuthor,
            constructors = (
                # This is called when
                Recipe.manage_addRecipeAuthorForm,
                # someone adds the product
                Recipe.manage_addRecipeAuthor
                ),
            icon = "www/author.gif"
            )

        registerIcon('comment.gif')
        registerIcon('newsletter.gif')
        registerIcon('receiver.gif')
        registerIcon('chef.gif')
        registerIcon('anonymous.gif')
        registerIcon('arrow.gif')
        registerIcon('smalllogo.gif')
        registerIcon('qmarkbig.gif')
        registerIcon('qmark.gif')
        registerIcon('emarkbig.gif')
        registerIcon('emark.gif')
        
        # tabs
        registerIcon('uncheckedleft.gif', epath='tabs')
        registerIcon('uncheckedright.gif', epath='tabs')
        registerIcon('checkedleft.gif', epath='tabs')
        registerIcon('checkedright.gif', epath='tabs')
        registerIcon('tabhighbar.gif', epath='tabs')

    except:
        """If you can't register the product, tell someone. 
        
        Zope will sometimes provide you with access to "broken product" and
        a backtrace of what went wrong, but not always; I think that only 
        works for errors caught in your main product module. 
        
        This code provides traceback for anything that happened in 
        registerClass(), assuming you're running Zope in debug mode."""
        import sys, traceback, string
        type, val, tb = sys.exc_info()
        sys.stderr.write(string.join(traceback.format_exception(type, val, tb), ''))
        del type, val, tb

import OFS, App

def registerIcon(filename, idreplacer={}, epath=None):
    # A helper function that takes an image filename (assumed
    # to live in a 'www' subdirectory of this package). It 
    # creates an ImageFile instance and adds it as an attribute
    # of misc_.MyPackage of the zope application object (note
    # that misc_.MyPackage has already been created by the product
    # initialization machinery by the time registerIcon is called).
    objectid = filename
    if epath is not None:
        path = "www/%s/"%epath
    else:
        path = "www/"
    
    for k,v in idreplacer.items():
        objectid = objectid.replace(k,v)
    setattr(OFS.misc_.misc_.RecipeProduct, 
            objectid, 
            App.ImageFile.ImageFile('%s%s' % (path, filename), globals())
            )
