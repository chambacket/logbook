document.addEventListener("DOMContentLoaded", () => {
    const navLinks = document.querySelectorAll("nav a")
  
    navLinks.forEach((link) => {
      link.addEventListener("click", (e) => {
        e.preventDefault()
        const targetId = link.getAttribute("href")
        const targetElement = document.querySelector(targetId)
  
        if (targetElement) {
          targetElement.scrollIntoView({
            behavior: "smooth",
          })
        }
      })
    })
  })
  
  