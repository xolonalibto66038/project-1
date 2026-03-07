// Get Stripe publishable key
fetch("/billing/config/")
.then((result) => { return result.json(); })
.then((data) => {
  // Initialize Stripe.js
  const stripe = Stripe(data.publicKey);

  let submitStripeBtn = document.querySelector("#submitStripeBtn");
  if (submitStripeBtn !== null) {
    submitStripeBtn.addEventListener("click", () => {
    console.log("Stripe button clicked");
    // Get Checkout Session ID
    fetch("/billing/create-checkout-session/")
      .then((result) => { return result.json(); })
      .then((data) => {
        console.log(data);
        // Redirect to Stripe Checkout
        return stripe.redirectToCheckout({sessionId: data.sessionId})
      })
      .then((res) => {
        console.log(res);
      });
    });
  }
});