function _inArray(element,arr){for(var i=0, len=arr.length;i<len;i++)if(arr[i]==element) return true;return false;}
function form2querystring(f){var text=tinyMCE.activeEditor.getContent();var skip_names=new Array();var add_text_name=null;if(text){skip_names = ['raw', 'raw:utf8:utext', 'raw:latin1:utext'];}
var is_mce_variable=function(v) {return v.substr(0,4)=="mce_";};
var d = '';for(i=0;i < f.elements.length;i++){ob=f.elements[i];if(is_mce_variable(ob.name)) continue;if((ob.type=='text' || ob.type=='textarea' || ob.type=='hidden') ||
(ob.type=='radio' && ob.checked)){if(ob.name!='') {if(_inArray(ob.name, skip_names)) add_text_name=ob.name;else d+=ob.name +'='+ escape(ob.value) +'&';}}else if(ob.type=='select-one'){d+=ob.name +'='+ escape(ob.options[ob.selectedIndex].value) +'&';}else if(ob.type=='select-multiple'){for (y=0;y < ob.options.length;y++)if(ob.options[y].selected)
d+=ob.name +'='+ escape(ob.options[y].value) +'&';}else if(ob.type=='checkbox'){if(ob.checked) d+=ob.name +'=1&';else d+=ob.name +'=False&';}}if(add_text_name && text)
d+=add_text_name +'='+ escape(text);return d;}
function ajaxSave(f){if(tinymce.majorVersion!='3') {alert("Using old version of ZTinyMCE. Upgrade to TinyMCE version 3 at least");return true;}
var ed=tinyMCE.activeEditor;_pre_save(ed);
tinymce.util.XHR.send({url : f.action,
type : 'POST',
content_type : 'application/x-www-form-urlencoded',
data : form2querystring(f),
async : false,
success : function(text) {_post_save(ed,text);},
error : function(type,req,o){if(type=='GENERAL'){alert("SERVER ERROR!\nWill submit form again without AJAX");f.onsubmit=null;
f.submit();}}});return false;}
function _pre_save(editor){editor.setProgressState(1);}
function _post_save(editor,response_text){editor.setProgressState(0);$('#savechangesbutton').val('Save changes');$('#savemessage').html(response_text);
fadetext("savemessage");hex=0;}