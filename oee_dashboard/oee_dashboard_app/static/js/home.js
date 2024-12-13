document.addEventListener("DOMContentLoaded", function () {
  let sidebar = document.querySelector(".sidebar");
  let closeBtn = document.querySelector("#btn");
  let searchBtn = document.querySelector(".bx-search");

  // Check if elements exist before adding event listeners
  if (closeBtn) {
    closeBtn.addEventListener("click", () => {
      sidebar.classList.toggle("open");
      menuBtnChange();
    });
  } else {
    console.warn("#btn element not found!");
  }

  if (searchBtn) {
    searchBtn.addEventListener("click", () => {
      sidebar.classList.toggle("open");
      menuBtnChange();
    });
  } else {
    console.warn(".bx-search element not found!");
  }

  function menuBtnChange() {
    if (sidebar.classList.contains("open")) {
      closeBtn?.classList.replace("bx-menu", "bx-menu-alt-right");
    } else {
      closeBtn?.classList.replace("bx-menu-alt-right", "bx-menu");
    }
  }
});
