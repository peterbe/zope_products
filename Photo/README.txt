Photo and Photo Folder

  Overview

    This product provides a Photo object and a Photo Folder object for
    managing digital images in Zope.  Photo objects provide multiple
    configurable sizes of the photo.  Photo Folders provide a way to manage a
    group of Photo objects by providing a way to specify display sizes and
    properties for all contained photos.
    
    This document has been updated for version 1.2.2.

  Installation

    Photo can be downloaded from the
    "Zope community site":http://www.zope.org/Members/rbickers/Photo/, or from
    "Source Forge":http://sourceforge.net/projects/zopephoto/.  Extract the
    distribution file in your Zope installation's Product directory.

    Photo requires the Python Image Library module (PIL) to be installed such
    that Zope can find it, or ImageMagic's 'convert' program in the path.  Visit
    the "PIL Web site":http://www.pythonware.com/products/pil/ for information
    on downloading and installing PIL, and the
    "ImageMagick Web site":http://www.imagemagick.org/ for information on
    ImageMagick.

  Photo

    Overview
    
      Photo objects provide a way to manage various display sizes of an image.
      They are very similar to Zope Image objects but generate and store
      multiple copies of the image in different sizes.  These sizes are
      configurable for each Photo.
      
    Displays

      A default set of display sizes are given to each new Photo object.
      These defaults can be overridden by configuring display sizes in a Photo
      Folder and adding Photos to that folder.  See the section on Photo
      Folders for more details.

      The default sizes are as follows::

                           Desired
        Display Name    Width x Height
        thumbnail         128 x  128
        xsmall            200 x  200
        small             320 x  320
        medium            480 x  480
        large             768 x  768
        xlarge           1024 x 1024

      Note that the dimensions are the *desired* dimensions.  When resized,
      each photo will be made as large as possible within the desired limits
      while still maintaining its aspect ratio.

      Making the width and height the same number will ensure that portrait
      and landscape images maintain a consistent physical size when displayed.
      For example, if you scan a standard 4x6 photograph taken with a camera
      in its normal position, and save it as a 1200w x 800h Photo, the
      *medium* display will resize to 480w x 320h.  A photograph taken with
      the camera sideways and saved as a 800w x 1200h image would be resized
      to 320w x 480h.  The same dimensions, just a different orientation.

      In contrast, if you configure a dimension such as 640w x 480h, the first
      photo would resize to 640w x 427h, and the second photo would resize to
      320w x 480h.  The size of these two rendered images is considerably
      different, even though the originals have the same dimensions (ignoring
      orientation).

      If you set both width and height to zero (0), the display size will be
      that of the original photo, but will have been processed by the engine.
      
    Settings

      Each photo has various settings that determine certain properties of the
      photo.  The following is a list of the available settings:

        * Store - determines the format for the image storage.  See Stores and
        Engines below for details.

        * Engine - determines which image rendering engine is used to create the
        different display sizes.  See Stores and Engines below for details.

        * Quality - this is the compression quality number from 1 to 100, 1
        being the worst image quality, 100 being the best.
        
        * Pregenerate Displays - determines if Photo should generate the
        displays when the Photo is created (and regenerate when it is updated),
        or if it should generate the displays on-the-fly when they are
        requested.

        * Display Cache Timeout - specifies the time in minutes that the
        displays should remain stored.  Zero (0) means never purge.  See the
        section on 'Display Cache' for details.

    Properties
    
      In addition to display sizes and settings, Photo objects provide
      configurable properties to associate information with each photo.  These
      properties are the same properties that many other Zope objects provide.
      The standard Properties tab is available for adding and deleting
      properties. However, the default management view displays a thumbnail of
      the image along with each defined property for one-screen access to
      updating the Photo information.  In this *Edit* view, property ids are
      displayed *capitalized* and *spacified*, which means a property with an id
      'photo_date' will display as 'Photo date'.

    Stores and Engines
    
      There are two options for storing the image data: 'Image' and 'ExtImage'.
      'Image' (the default) uses Zopes built in Image object to store the images
      in the ZODB.  'ExtImage' uses the ExtFile/Image product to store the image
      files on the file system.  For this option, you must have ExtFile/Image
      installed and configured.  Once a store is chosen for a photo, it cannot
      be changed without deleting and recreating the photo.

      IMPORTANT NOTE: Zope 2.4.0 has a bug which prevents ExtImage from properly
      handling copying and pasting objects. You should not use Zope 2.4.0 with
      the ExtImage option.  Zope 2.4.1 with ExtImage 1.1.3 works properly, as
      does Zope 2.3.

      There are also two options for the engine to use for rendering display
      sizes: 'PIL' and 'ImageMagick'.  'PIL' uses the Python Imaging Library.
      This option is relatively fast, but the images it produces are not the
      best quality, with features such as edges that are not smooth.
      'ImageMagick' produces much smoother images at the expense of performance.
      It can take quite a bit longer to produce displays with 'ImageMagick' over
      using 'PIL' depending on your hardware and the image itself.  Also, there
      is no up to date Python module support for 'ImageMagick'.  Photo runs an
      external program to process the images.  This may or may not work on your
      system.  Because of ImageMagick's superior rendering quality, ImageMagick
      is the default engine.
      
    Display Cache

      Photo objects consist of the original image and a series of configurable
      display sizes that are generated from the original image.  These display
      sizes are stored in the database (or as separate files if you're using
      ExtImage) for faster retrieval since rendering displays can be resource
      intensive and time consuming.  However, since many of the display sizes
      may never be viewed, or may be viewed infrequently, Photo allows you to
      choose whether or not to generate these displays when the Photo is
      created, or to generate them on-the-fly when they are requested.  In
      addition, if you choose to generate them on-the-fly, you can optionally
      set a timeout (in minutes) to purge the display from storage.

      If you select the 'Pregenerate Displays' option, all display sizes will be
      generated when the Photo is added and all of them will be regenerated when
      the Photo is updated.  If the 'Pregenerate Displays' option is not chosen,
      the displays will only be created when the display is requested.

      Note that if the 'Pregenerate Displays' option is not chosen, the
      'Regenerate All' option in the 'Displays' tab will not generate displays
      that have not already been generated.  The 'Purge All' option will remove
      all generated displays from storage, regardless of the 'Pregenerate
      Displays' setting.  In any case, if a display is requested, and has not
      been generated, it will be generated on-the-fly.

      If you set a timeout, Photo will purge displays whose age exceeds the
      timeout.  Purging is done as follows:

        When a display is requested, Photo checks the age of the display.  If it
        is greater than half of the timeout setting, Photo a) resets the age of
        the requested display to zero, and b) purges any displays in that Photo
        object whose age is greater than the timeout.
        
        The 'Clean Up' option can be used to force a purge.  If a display's age
        is greater than the timeout, it will be purged.  Otherwise it will
        remain unchanged.  If you want to exclude a particular display or
        displays from being purged, you can 'check' those displays before
        selecting 'Clean Up'.

        You can force all displays to be purged regardless of their age using
        the 'Purge All' option.  If you want to exclude a particular display or
        displays from being purged, you can 'check' those displays before
        selecting 'Purge All'.

      Because purging a display does not actually remove it from the database
      (ZODB is an append only database), you'll need to pack regularly if your
      timeout is low and many displays are generated and purged.  A timeout of
      several days (depending on site traffic) is recommended.

    Usage (API)

      Photo objects provide several methods for viewing the different display
      sizes and to assist in creating navigable Web pages.

      * tag(display=None, height=None, width=None, cookie=0, alt=None,
            css_class=None, **kw)

        Inserts an HTML img tag to display the image.  If 'display' is
        specified, the image will be shown in that display size.  If it is not
        specified, or if the display doesn't exist, the original image is
        displayed.  'height' and 'width' are currently not used, but may in
        future releases allow for on-the-fly resizing of images.  If 'cookie'
        is true, and 'display' is specified, Photo will set a browser cookie
        to save the display size.  If 'cookie' is true, and 'display' is *not*
        specified, the Photo will be displayed in the size specified by the
        browser cookie.  If the cookie is not set, the original image will be
        displayed.  The 'alt', 'css_class', and additional keyword arguments
        will add 'alt', 'class', and additional attributes to the image tag.
        If 'alt' is not specified, the Photo's 'title' or 'id' will be used.
        The additional attributes are useful for adding things such as
        'border=1' to provide a border around the image.

      * exttag(prefix, display=None, cookie=0, alt=None, css_class=None, **kw)

        Inserts an HTML img tag to display the image via a server other than
        Zope.  This option only makes sense for the 'ExtImage' store.  The
        'prefix' is a URL that the image server can use to read files from the
        'ExtImage' repository.  The 'src' attribute of the img tag will be
        'prefix' + the filename of the requested display size as stored by
        'ExtImage'.  If 'display' is specified, the tag will use the file for
        that display size.  If it is not specified, or if the display doesn't
        exist, the original image file will be used.  If 'cookie' is true, and
        'display' is specified, Photo will set a browser cookie to save the
        display size.  If 'cookie' is true, and 'display' is *not* specified,
        the Photo will be displayed in the size specified by the browser cookie.
        If the cookie is not set, the original image will be displayed.  The
        'alt', 'css_class', and additional keyword arguments will add 'alt',
        'class', and additional attributes to the image tag. If 'alt' is not
        specified, the Photo's 'title' or 'id' will be used. The additional
        attributes are useful for adding things such as 'border=1' to provide a
        border around the image.

      * displayIds(exclude=('thumbnail',))

        Returns a list of display ids, excluding those specified by 'exclude'.
        This is useful for creating a list of available display sizes from
        which to choose.  The default is to exclude 'thumbnail' since it is
        normally not wanted as an option for viewing a Photo.  The list is
        sorted by the smallest display image in bytes.

      * displayLinks(exclude=('thumbnail',))

        Returns a list of HTML link tags for each display size.  For example::

          <a href="http://localhost/myphoto.jpg/view?display=small">small</a>

        This is useful for providing quick links to the different display
        sizes.  The list is sorted by the smallest display image in bytes.
        See 'displayIds' for an explanation of 'exclude'.

      * nextPhoto()

        Returns the next Photo object in the current folder, or 'None' if this
        is the last object.  Objects are sorted by id.  This is useful for
        providing navigational links to adjacent photos.  For example::

          <dtml-with nextPhoto>
            <a href="&dtml-absolute_url;/view"><dtml-var title_or_id></a>
          </dtml-with>

      * prevPhoto()

        Returns the previous Photo object in the current folder, or 'None' if
        this is the first object.  Objects are sorted by id.  This is useful
        for providing navigational links to adjacent photos.  See 'nextPhoto'
        for an example.

      In addition to the configured properties, Photo objects also have a few
      properties that are not configurable:
      
      * content_type
      
        The content type of the image.

      * width

        The width, in pixels, of the original uploaded image.

      * height

        The height, in pixels, of the original uploaded image.

      * size

        The size, in bytes, of the original uploaded image.

  Photo Folder

    Overview

      Photo Folder objects help manage a group of Photo objects by providing
      an interface for adding, removing, and modifying the properties and
      display sizes off all contained photos, and by providing defaults for
      newly created photos.  It is not required that Photo objects be created
      inside of a Photo Folder.  They will function properly in a normal
      folder.  However, if you do not use Photo Folders, you will have to
      modify properties and display sizes of each individual Photo once it has
      been added.

    Displays

      The 'Displays' tab in the Photo Folder management interface is where you
      manage display sizes for contained photos.  See the displays section under
      'Photo' for details on displays.

      The displays in the Photo Folder will be used as the default displays
      for each new Photo object that is added to that Photo Folder.  If you
      add a display, every Photo object contained in the folder will be given
      the new display.  If the display already exists in a particular photo,
      it will be left unmodified.  If you delete a display, every contained
      Photo object will have that display size removed.  If the display does
      not exist in a particular photo, it will be ignored.  If you modify a
      display, every contained photo that has the modified displays will be
      updated to reflect the new width and height.  If a photo does not have
      the displays modified, it will be ignored.  The display will not be
      added.
      
    Properties

      Photo Folders have two tabs for properites:  the standard 'Properties'
      tab, and a 'Photo Properties' tab.

      * Properties Tab

        The standard 'Properties' tab is where Photo Folder properties are
        created as is done with many other Zope objects.  These might include
        a 'title' and 'description' for the collection of photos, or an
        'image' that specifies a representative photo from the collection to
        display when listing multiple Photo Folders.

      * Photo Properties Tab

        The 'Photo Properties' tab provides two sections relating to the Photo
        objects contained in the Photo Folder:  'Default Settings' and 'Photo
        Properties'.
        
        The 'Default Settings' provides newly created Photo objects with default
        values for their settings as well as allows you to modify the settings
        for all contained Photos.  See the Photo object documentation for
        details on the available settings.
        
        The 'Photo Properties' is very similar to a standard 'Properties',
        except that the properties apply to the contained Photo objects.  When
        you add a property, the property is added to all contained Photo objects
        with the given value.  If a particular photo already has the added
        property, it is left unmodified for that photo.  When you delete a
        property, the property is deleted from all contained Photo objects. If a
        particular photo doesn't have that property, it is ignored. Modifying
        property values in this screen will *not* change property values for any
        contained photos, but new photos added to this Photo Folder will be
        given the new value for the modified property.  When you add a new Photo
        object to a Photo Folder, it has a 'title' property plus all of the
        properties and values listed on this screen.

    Usage (API)

      Photo Folder objects provide a few helper methods to assist in creating
      views of the contained folders.

      * numPhotos()

        Returns the number of Photo objects in the Photo Folder.

      * nextPhotoFolder()

        Returns the next Photo Folder object in the current folder, or 'None'
        if this is the last object.  Objects are sorted by id.  This is useful
        for providing navigational links to adjacent Photo Folders.  For
        example::

          <dtml-with nextPhotoFolder>
            <a href="&dtml-absolute_url;"><dtml-var title_or_id></a>
          </dtml-with>

      * prevPhotoFolder()

        Returns the previous Photo Folder object in the current folder, or
        'None' if this is the first object.  Objects are sorted by id.  This
        is useful for providing navigational links to adjacent Photo Folders.
        See 'nextPhotoFolder' for an example.
        
  Converting Image Objects to Photo Objects

    You can convert existing Zope Image objects to Photo objects with the
    following Python Script::

      """Convert all Image objects in folder to Photo objects"""

      for image in context.objectValues(['Image']):
          context.manage_delObjects([image.getId(),], REQUEST=context.REQUEST)
          context.manage_addProduct['Photo'].manage_addPhoto(image.getId(),
                             image.title, image.data, REQUEST=context.REQUEST)

    If you save this script as 'Image2Photo', you can run it on a folder with
    Image objects to convert them.  For example, if you have images in
    /Personal/Photos, you can run http://myhost/Personal/Photos/Image2Photo.
    
  FTP/WebDAV Support
  
    Photos can be transferred via FTP/WebDAV.  If you upload an image file to an
    existing Photo Folder, a Photo object will be created using the default
    settings provided by the Photo Folder.  If you upload an image file to an
    existing Photo object, only the image data itself will be updated and the
    displays will be rerendered.  Downloading from a Photo object will get the
    original image file.

  Notes

    * There is no internal link or association between a Photo Folder and a
    contained Photo.  Photo objects can be created, copied and pasted outside
    of Photo Folders and they will still function properly.  If you paste a
    Photo inside a Photo Folder and the folder 'Photo Properties' and
    'Displays' do not correspond with those of the pasted Photo, the photo
    will *not* be modified.  It's up to you to modify the photo to bring it in
    sync with the folder.  Future versions may provide a method of
    syncronizing contained folders for this case.

    * Rendering display sizes takes time, especially with the 'ImageMagick'
    engine option.  It is most efficient to create a Photo Folder, set the
    display sizes and properties as desired, and then add new Photo objects.
    When you add or modify Photo Folder display sizes, each contained photo must
    be updated by regenerating the display sizes, which can be a slow process if
    there are many photos.  This is minimized somewhat by only regenerating the
    display sizes that were modified.

    * When you add a Photo Folder, you are given the option to create sample
    views.  This will create two DTML Methods, named 'index_html' and 'view'.
    'index_html' will display the 'thumbnail' size of the contained photos and
    provide a link to view the photo using the 'view' method.  The 'view'
    method allows you to view the photo in its various sizes and provides
    links to the previous and next photos in the folder.  Neither output is
    very pretty, but you can use these to help construct your own view
    methods.

    * Currently, "contained" Photo objects means that the Photo object is
    directly in the Photo Folder.  'Photo Properties' and 'Displays' settings
    of a Photo Folder do not apply to sub folders and their Photo objects.

  More Information

    Visit the "Source Forge site":http://sourceforge.net/projects/zopephoto/
    for questions, comments, bug reports, the latest release, and CVS access.
    You may also visit the
    "Zope community Web site":http://www.zope.org/Members/rbickers/Photo/.
