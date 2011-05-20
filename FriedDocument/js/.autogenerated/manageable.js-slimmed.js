function renameObjects(f){var count_changes=0;var ids=__listify_singletons(f['ids:list']);for(var i=0,len=ids.length;i<len;i++){if(ids[i].checked) {if(_renameObject(ids[i].value, f)) 
count_changes++;}}if(count_changes){f.action="saveObjectRenames";f.submit();}}
function stripSpaces(x){return x.replace(/^\s+|\s+$/g,'');}

function $E(tagName){return document.createElement(tagName);}

function $T(text){return document.createTextNode(text);}
function id$(){var elements=new Array();for(var i=0;i < arguments.length;i++){var element=arguments[i];if(typeof element == 'string')
element=document.getElementById(element);if(arguments.length==1) 
return element;elements.push(element);}
return elements;}
function _renameObject(id,f){var change_made=false;var previd;if(id$('newid-'+id))
previd=id$('newid-'+id).value;else
previd=id;var newid=prompt("New ID", previd);newid=stripSpaces(newid);var prevtitle=f['titleof-' + id].value;var newtitle=prompt("New Title (optional)", prevtitle);if(newtitle!=null)if(newtitle != f['titleof-' + id].value){f['titleof-' + id].value=stripSpaces(newtitle);change_made=true;}if(newid!=previd){change_made=true;if(id$('newid-'+id))
id$('newid-'+id).value=newid;else{var newhiddeninput=document.createElement('input');newhiddeninput.setAttribute('type','hidden');
newhiddeninput.setAttribute('name','newid-' + id);newhiddeninput.setAttribute('value',newid);
f.appendChild(newhiddeninput);}}
return change_made;}
function copyObjects(f){var ids=__listify_singletons(f['ids:list']);var count=0;for(var i=0,len=ids.length;i<len;i++)if(ids[i].checked) 
count++;if(count){f.action="copyObjectsSelected";f.submit();} else 
alert("Select which objects you want to copy");}
function cutObjects(f){var ids=__listify_singletons(f['ids:list']);var count=0;for(var i=0,len=ids.length;i<len;i++)if(ids[i].checked) 
count++;if(count){f.action="cutObjectsSelected";f.submit();} else 
alert("Select which objects you want to cut");}
function pasteObjects(f){f.action="pasteObjectsSelected";f.submit();}
function deleteObjects(f){var ids=__listify_singletons(f['ids:list']);var count=0;for(var i=0,len=ids.length;i<len;i++)if(ids[i].checked) 
count++;if(count){if(count==1)
var msg = "Delete this object permanently?";else 
var msg = "Delete these "+ count +" objects permanently?";if(confirm(msg)){f.action="deleteObjectsSelected";f.submit();}} else 
alert("Select which objects you want to delete");}

function __listify_singletons(obj){if(obj.length==null)
return new Array(obj);if(obj.length) 
return obj;}
function _hL(imgelement){imgelement.src=imgelement.src.replace('_off','');}
function _uhL(imgelement){imgelement.src=imgelement.src.replace('.gif','_off.gif');}
function _ajaxsort(id,direction){xmlhttpPost('reorderFriedObject', 'id='+escape(id)+'&ajax_return=1&direction='+direction,
function(res) {if(res.responseText.indexOf('ajax_error:')==0)
alert(res.responseText.replace('ajax_error:','Error:'));else
id$('objectlisttable').innerHTML=res.responseText;});
return false;}
function _basename(v){return v.substring(Math.max(v.lastIndexOf('/'), 
v.lastIndexOf('\\'), 
v.lastIndexOf(':'))+1);}
function suggestId(title_input_element,id_input_element,filepath){var v=title_input_element.value;if(!v) 
alert("Please enter a file first");else if(filepath!=null){id_input_element.value=_basename(v);}else{xmlhttpPost('../manage_addProduct/FriedDocument/manage_suggestIdFromTitle', 
'title='+escape(v),function(res) {if(res.responseText)
id_input_element.value=res.responseText;});}}
function ajaxsortup(id){return _ajaxsort(id, 'up');}
function ajaxsortdown(id){return _ajaxsort(id, 'down');}
function showElement(el){if(typeof el=="string"){el=id$(el);}if(el.style['display']=='none'){el.style['display']='';}}
function hideElement(el){if(typeof el=="string"){el=id$(el);}if(id$(el).style['display']==''){id$(el).style['display']='none';}}
function highlightAccess(on_id,off_id){var on=id$(on_id);var off=id$(off_id);off.className = 'shaded';on.className = 'notshaded';}
function checkAddDocumentForm(f){var title=stripSpaces(f.title.value);var id=stripSpaces(f.id.value);var metalmacro=stripSpaces(f.metalmacro.value);var belike_path=stripSpaces(f.belike_path.value);if(!title && !id){alert("Please enter a Name or Id");}else if(!metalmacro && !belike_path){alert("Please enter the Metalmacro");} else return true;return false}
function randstr(){return (""+Math.random()*10).slice(2);}
function changePreviewImage(display){var img=id$('fd-imagepreview');var src=img.src;if(display){if(src.indexOf('display=') > -1) {src=src.replace(/display=\w+/g, 'display='+display);}else{if(src.indexOf('?')==-1)
src+='?display=' + display;else
src+='&display=' + display;}}else{if(src.indexOf('display=') > -1){src=src.replace(/display=\w+/g, '');}}
src=src.replace(/&randstr=\d+/,'');src+='&randstr=' + randstr();img.src=src;return false;}
function action_pleasewait(){var container;if(id$('action_pleasewait')){var newimg = $E('img');newimg.border="0";
newimg.alt="Please wait...";newimg.src="/misc_/FriedDocument/progress-wheel.gif";
id$('action_pleasewait').appendChild(newimg);var p = $E('p');p.appendChild($T('Please wait...'));id$('action_pleasewait').appendChild(p);
showElement(id$('action_pleasewait'));}}