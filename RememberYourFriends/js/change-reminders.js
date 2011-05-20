function colourTrash(el) {
   el.src = "/misc_/RememberYourFriends/trash_colour.gif";
}
function uncolourTrash(el) {
   el.src = "/misc_/RememberYourFriends/trash.gif";
}
function editthis(id) { location.href=location.href.split('?')[0]+'?rid='+id; }
function cancelexit(id) { location.href=location.href.split('?')[0]; }

function confirmDelete(name, email) {
   var msg;
   if (name && email) {
      msg = "Delete reminder to "+name+" ("+email+")?";
   } else if (email) {
      msg = "Delete reminder to "+email+"?";
  } else {
     msg = "Delete reminder to "+name+"?";
  }
   var certainty = confirm(msg);
   return certainty;
}
function __string_count(what, where) {
   return where.split(what).length - 1; 
}
function __ok_email(e) {
   if (e.indexOf(' ')>-1 || __string_count('@',e)!=1 || __string_count('.',e)<1)
     return false;
   return true;
}
function checkAddReminder(f) {
   var n = $.trim(f.name.value);
   var e = $.trim(f.email.value);
   if ((n+e).length==0) {
      alert("Please enter your friends name or email");
      return false;
   }
   if (e)
     if (!__ok_email(e)) {
        alert("Please enter a valid email address");
        return false;
     }
   return true;
}

// because Firefox sometimes "caches" input into forms
// even if the HTML doesn't contain it, then we'll make
// sure the savebutton isn't hidden in case there is already
// something filled in in the addform.
$(function() {
   if ($.id('addform'))
     if ($.id('savebutton'))
       if ($.id('savebutton').className='h' && ($.id('addform').name.value || $.id('addform').email.value))
         $.id('savebutton').className='';
});


function checkEditReminder(f) {
   var n = $.trim(f.name.value);
   var e = $.trim(f.email.value);
   if ((n+e).length==0) {
      alert("Please enter your friends name or email");
      return false;
   }
   
   if (e)
     if (!__ok_email(e)) {
        alert("Please enter a valid email address");
        return false;
     }
   if (f.dob != null && f.dob.value) {
      var dob = f.dob.value;
      
      var this_year_int = new Date().getFullYear();
      var this_year = this_year_int.toString();
      if (dob.indexOf(this_year)>-1) {
         var yes_this_year = prompt("Was your friend really born this year?\nIf not, change it or leave it blank", this_year);
         if (yes_this_year == null) return false;
         if (yes_this_year && yes_this_year.length==2) {
            var k = confirm("Did you mean 19"+yes_this_year+"?");
            if (k) yes_this_year = "19" + yes_this_year;
            else {
               var y = confirm("So you meant 20"+yes_this_year+"?");
               if (y) yes_this_year = "20" + yes_this_year;
               else return false;
            }
         }
         f.dob.value = dob.replace(this_year, yes_this_year);
      }
   }
   return true;
}