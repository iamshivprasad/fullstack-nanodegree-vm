function signOut() {
    var auth2 = gapi.auth2.getAuthInstance();
    auth2.signOut().then(function () {
      console.log('User signed out.');
    });
    $.ajax(
      {
        url: '/gdisconnect',
        success: function (result) {
          if (result) {
            var obj = jQuery.parseJSON(result);
            $('#result').html(obj.message + '. Redirecting...')
            setTimeout(function () {
              window.location.href = "/";
            }, 1000);
          }
          else {
            console.log('Failed to signed out.');
          }
        }
      }
    );
  }
