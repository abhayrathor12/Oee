let sidebar = document.querySelector(".sidebar");
let closeBtn = document.querySelector("#btn");
let searchBtn = document.querySelector(".bx-search");


closeBtn.addEventListener("click", () => {
  sidebar.classList.toggle("open");
  menuBtnChange();//calling the function(optional)
});

searchBtn.addEventListener("click", () => { // Sidebar open when you click on the search iocn
  sidebar.classList.toggle("open");
  menuBtnChange(); //calling the function(optional)
});

function closePopup1() {
  document.getElementById("popupDiv1").style.display = "none";
}

function closePopup() {
  document.getElementById("popupDiv").style.display = "none";
}

function showPopup() {
  document.getElementById("popupDiv").style.display = "block";
}


function closePopup2() {
  document.getElementById("popupDiv2").style.display = "none";
}

function showPopup2() {
  document.getElementById("popupDiv2").style.display = "block";
}

function closePopup3() {
  document.getElementById("popupDiv3").style.display = "none";
}

function showPopup3() {
  document.getElementById("popupDiv3").style.display = "block";
}

function validateForm(event) {
  const radio1 = document.getElementById("radio1");
  const radio2 = document.getElementById("radio2");
  const radio3 = document.getElementById("radio6");
  const radio4 = document.getElementById("radio5");

  if (!radio1.checked && !radio2.checked && !radio3.checked && !radio4.checked) {
    showPopup3();
    event.preventDefault(); // Prevent the form from submitting
  }
  else if (!radio1.checked && !radio2.checked) {
    showPopup();
    event.preventDefault(); // Prevent the form from submitting
  }
  else if (!radio3.checked && !radio4.checked) {
    showPopup2();
    event.preventDefault(); // Prevent the form from submitting
  }
};

function handelradioclick(radioId) {
  if (radioId === "radio6") {
    document.getElementById("radio5").checked = false;
  }
  else if (radioId === "radio5") {
    document.getElementById("radio6").checked = false;
  }
}

// following are the code to change sidebar button(optional)
function menuBtnChange() {
  if (sidebar.classList.contains("open")) {
    closeBtn.classList.replace("bx-menu", "bx-menu-alt-right");//replacing the iocns class
  } else {
    closeBtn.classList.replace("bx-menu-alt-right", "bx-menu");//replacing the iocns class
  }
}

function disableFields(disable) {
  var select = document.getElementById("myList");
  var start = document.getElementsByName("start")[0];
  var end = document.getElementsByName("end")[0];

  select.disabled = disable;
  start.disabled = !disable;
  end.disabled = !disable;
}



$(window).on("load resize ", function () {
  var scrollWidth = $('.tbl-content').width() - $('.tbl-content table').width();
  $('.tbl-header').css({ 'padding-right': scrollWidth });
}).resize();