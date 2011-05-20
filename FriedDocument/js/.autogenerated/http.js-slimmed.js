function queryFromForm(form){var data = '';var element;var lastelementname = '';for(var i=form.elements.length-1;i > -1 ; i--){element=form.elements[i];switch (element.type) {case 'text':
case 'hidden':
case 'password':
case 'textarea':
case 'select-one':
data+=element.name + '=' + encodeURIComponent(element.value) + '&'
break;case 'radio':if(element.checked){data+=element.name + '=' + encodeURIComponent(element.value) + '&'}
break;case 'checkbox':if(element.checked){if(element.name==lastelementname) {if(data.lastIndexOf('&')==data.length-1){data=data.substr(0, data.length - 1);}
data+=',' + encodeURIComponent(element.value);}else{data+=element.name + '=' + encodeURIComponent(element.value);}
data+='&';lastelementname=element.name;}
break;}}
data=data.substr(0, data.length - 1);return data;}    
function xmlhttpPost(url,data,callback){var xmlHttpReq=false;if(window.XMLHttpRequest){xmlHttpReq=new XMLHttpRequest();}else if(window.ActiveXObject){xmlHttpReq=new ActiveXObject("Microsoft.XMLHTTP");} 
xmlHttpReq.open('POST', url, true);xmlHttpReq.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');xmlHttpReq.onreadystatechange=function(){if(xmlHttpReq.readyState==4){switch (xmlHttpReq.status) {case 200:
callback(xmlHttpReq)
break
case 404:
alert('Error: Not Found.  ' + url)
break;default:
document.body.innerHTML=xmlHttpReq.responseText;break;}}}
xmlHttpReq.send(data);}
function ajaxFormSubmit(f){var qs=queryFromForm(f);qs+='&ajax_return=1';var url=f.action;var callbackfunction=function(){};if(arguments.length>1){callbackfunction=arguments[1];}
xmlhttpPost(url,qs,callbackfunction);return false;}