$(document).ready(()=>{
	$("#login_btn").click(()=>{
		let username = $("#inputUsername").val();
		let password = $("#inputPw").val();
		let csrf_token = $("#csrf_token").val();
		$.ajax({
			url: "/login",
			type: "post",
			contentType: "application/x-www-form-urlencoded",
			data: {username: username, password: password, csrf_token: csrf_token},
			success: (response)=>{
				if (response.redirect_url) {
					window.location.href = response.redirect_url;
				} else {
					$(".error-box").empty();
					$(".error-box").append("<p>" + response.message + "</p");
					$(".error-box").show();
				};
			}
		})
	})
})