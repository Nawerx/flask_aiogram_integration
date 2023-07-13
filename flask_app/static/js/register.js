const pwField = document.querySelector("#inputPw"),
    confirmPW = document.querySelector("#confirmPw"),
    btn = document.querySelector("#signup_btn")


pwField.addEventListener("input", ()=>{
    let inpValue = pwField.value;
    if (inpValue.length >= 8) {
        confirmPW.removeAttribute("disabled")
    } else {
			confirmPW.value = "";
			confirmPW.setAttribute("disabled", "");
			btn.setAttribute("disabled", "")
		}
});

confirmPW.addEventListener("input", ()=>{
    let inpValue = confirmPW.value;
    if (pwField.value == inpValue) {
        btn.removeAttribute("disabled");
    } else {
			btn.setAttribute("disabled", "");
		}
});


$(document).ready(()=>{
	$("#signup_btn").click(()=>{
		let username = $("#inputUsername").val();
		let password = $("#inputPw").val();
		let password_repeat = $("#confirmPw").val();
		let csrf_token = $("#csrf_token").val();
		$.ajax({
			url: "/register",
			type: "post",
			contentType: "application/x-www-form-urlencoded",
			data: {username: username, password: password, password_repeat: password_repeat, csrf_token: csrf_token},
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