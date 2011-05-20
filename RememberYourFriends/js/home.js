$(function() {
   $.get('show_sent_reminders', {limit:20}, function(data) {
      if (data) $('#formorlog').html(data);
      });
});
function validateSignup(f) {
   var email = f.email.value;
   if (!email) {
      alert("Please enter your email address to sign up.");
      return false;
   } else if (email.indexOf(' ')!=-1) {
      alert("Email appears invalid. It cannot contain spaces. Please check.");
      return false;
   } else if (email.indexOf('@')==-1) {
      alert("Email appears invalid. Please check.");
      return false;
   }
   return true;
}

$(function() {
  var inps=$('input');
  
  inps.each(function() {
    if (this.name=='friends.name:records') {
      //var nameid=inps[i].id;
      //var selectid = 'periodicity' + parseInt(nameid.replace('name',''));
      this.onblur=function(){
        if(!this.value){
	  this.className='unfocused';
	  selectid = 'periodicity' + parseInt(this.id.replace('name',''));
	  document.getElementById(selectid).className='unfocused';
	}
      };
      this.onfocus=function(){
        this.className='focused';
	selectid = 'periodicity' + parseInt(this.id.replace('name',''));
	document.getElementById(selectid).className='focused';
      };      
    }
  });
   
});

function readmore() {
   $('#moreintroduction').removeClass('h');
   $('#readmoreintroduction').addClass('h');
   return false;
}