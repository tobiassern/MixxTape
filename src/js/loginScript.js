function signInCallback(authResult) {
	redirect_url = $.urlParam('redirect');
	if(redirect_url == null) {
		redirect_url = '/'
	}
	if (authResult['code']) {
    	// Hide the sign-in button now that the user is authorized
    	$('#signinButton').attr('style', 'display: none');
    	// Send the one-time-use code to the server, if the server responds, write a 'login successful' message to the web page and then redirect back to the main restaurants page
    	var loginstate = $('#result').attr('data-loginstate');
    	$.ajax({
      		type: 'POST',
      		url: '/gconnect?state=' + loginstate,
      		processData: false,
      		data: authResult['code'],
      		contentType: 'application/octet-stream; charset=utf-8',
      		success: function(result) {
        		// Handle or verify the server response if necessary.
        		if (result) {
      				window.location.href = redirect_url;
      			} else if (authResult['error']) {
    				console.log('There was an error: ' + authResult['error']);
  				} else {
        			$('#result').html('Failed to make a server-side call. Check your configuration and console.');
         		}
      		}
      	});
    }
}

$.urlParam = function(name){
    var results = new RegExp('[\?&]' + name + '=([^&#]*)').exec(window.location.href);
    if (results==null){
       return null;
    }
    else{
       return results[1] || 0;
    }
}