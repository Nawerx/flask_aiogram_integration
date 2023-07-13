$(document).ready(() => {
  $(".verify").click(() => {
    let username = String($(".verify").data("username"));
    $.ajax({
      url: "/verify",
      type: "post",
      contentType: "application/json",
      data: JSON.stringify({ username: username, action: "confirm" }),
      success: (response) => {
        $('.container').empty();
        $('.container').append("<p>Your email was successfully verified. Redirecting to your profile in </p>");
        $('.container').append("<h1 class='counter'>5 seconds...</h1>");

        let counter = 5;
        let countdownInterval = setInterval(() => {
          counter--;
          $('.counter').text(`${counter} seconds...`);
          if (counter === 0) {
            clearInterval(countdownInterval);
            window.location.href = response.redirect_url;
          }
        }, 1000);
      }
    });
  });
});
