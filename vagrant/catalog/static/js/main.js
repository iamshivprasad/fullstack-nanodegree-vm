
document.getElementById("customBtn").addEventListener('click', function(){
    auth2.grantOfflineAccess({ 'redirect_uri': 'postmessage' }).then(signInCallback);
});


function signInCallback(json) {
  console.log('inside callback fuction');
  console.log(json);
  authResult = json;
  if (authResult['code']) {
    $('#customBtn').text("Singin in...")
    $.ajax({
      type: 'POST',
      url: '/oauth/google?state={{STATE}}',
      processData: false,
      data: authResult['code'],
      contentType: 'application/octet-stream; charset=utf-8',
      success: function (result) {
        if (result) {
          var obj = jQuery.parseJSON(result);
          $('#result').html('Login Successful!</br>' + obj.name + '</br>Redirecting...')
          setTimeout(function () {
            window.location.href = "/";
          }, 4000);

        } else if (authResult['error']) {
          console.log('There was an error: ' + authResult['error']);
        } else {
          $('#result').html('Failed to make a server-side call. Check your configuration and console.');
        }
      }

    });
  }
}