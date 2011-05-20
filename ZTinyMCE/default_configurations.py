default_configurations = (


dict(name='simple.conf', config='''
mode : "textareas",
theme : "simple"
'''
),

dict(name='advanced.conf', config='''
language : "en",
mode : "textareas",
theme : "advanced",
plugins : "table,save,advhr,advimage,advlink,emotions,iespell,insertdatetime,preview,zoom,flash,searchreplace,print,contextmenu,paste,directionality,fullscreen,noneditable",
theme_advanced_buttons1_add_before : "save,newdocument,separator",
theme_advanced_buttons1_add : "fontselect,fontsizeselect",
theme_advanced_buttons2_add : "separator,insertdate,inserttime,preview,separator,forecolor,backcolor",
theme_advanced_buttons2_add_before: "cut,copy,paste,pastetext,pasteword,separator,search,replace,separator",
theme_advanced_buttons3_add_before : "tablecontrols,separator",
theme_advanced_buttons3_add : "emotions,iespell,flash,advhr,separator,print,separator,ltr,rtl,separator,fullscreen",
theme_advanced_toolbar_location : "top",
theme_advanced_toolbar_align : "left",
theme_advanced_path_location : "bottom",
//content_css : "/example_data/example_full.css",
plugin_insertdate_dateFormat : "%Y-%m-%d",
plugin_insertdate_timeFormat : "%H:%M:%S",
extended_valid_elements : "hr[class|width|size|noshade],font[face|size|color|style],span[class|align|style]",
//external_link_list_url : "example_data/example_link_list.js",
//external_image_list_url : "example_data/example_image_list.js",
//flash_external_list_url : "example_data/example_flash_list.js",
//file_browser_callback : "mcFileManager.filebrowserCallBack",
theme_advanced_resize_horizontal : false,
theme_advanced_resizing : true
'''
),




)