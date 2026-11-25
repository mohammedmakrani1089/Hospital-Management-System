
document.addEventListener("DOMContentLoaded", function () {

    // ==========================================
    // 1. GET HTML ELEMENTS
    // ==========================================

    const payButton = document.getElementById("payNowButton");

    const paymentConfig = document.getElementById("razorpayConfig");

    const verificationForm = document.getElementById(
        "razorpayVerificationForm"
    );

    const statusMessage = document.getElementById(
        "paymentStatusMessage"
    );


    if (!payButton || !paymentConfig || !verificationForm) {

        console.error("Payment HTML elements are missing!");

        return;

    }


    // ==========================================
    // 2. GET RAZORPAY ORDER DETAILS
    // ==========================================

    const keyId = paymentConfig.dataset.key;

    const amount = Number(paymentConfig.dataset.amount);

    const currency = paymentConfig.dataset.currency;

    const orderId = paymentConfig.dataset.orderId;


    if (!keyId || !amount || !orderId) {

        statusMessage.textContent =
            "Payment configuration is incomplete. Please refresh the page.";

        return;

    }


    // ==========================================
    // 3. SHOW PAYMENT MESSAGE
    // ==========================================

    function showMessage(message) {

        if (statusMessage) {

            statusMessage.textContent = message;

        }

    }


    // ==========================================
    // 4. OPEN RAZORPAY CHECKOUT
    // ==========================================

    payButton.addEventListener("click", function () {

        if (typeof Razorpay === "undefined") {

            showMessage(
                "Payment gateway could not be loaded. Please refresh the page."
            );

            return;

        }


        payButton.disabled = true;

        payButton.innerHTML =
            'Opening Secure Payment... <i class="fa-solid fa-spinner fa-spin"></i>';


        // Razorpay Checkout Configuration
        const options = {

            key: keyId,

            amount: amount,

            currency: currency,

            name: "Hospital Management",

            description: "Doctor Consultation Payment",

            order_id: orderId,

            timeout: 600,

            retry: {
                enabled: true
            },

            theme: {
                color: "#2563eb"
            },


            // ==========================================
            // 5. PAYMENT SUCCESS HANDLER
            // ==========================================

            handler: function (response) {

                showMessage(
                    "Payment received. Verifying securely..."
                );

                verificationForm.querySelector(
                    '[name="razorpay_payment_id"]'
                ).value = response.razorpay_payment_id;

                verificationForm.querySelector(
                    '[name="razorpay_order_id"]'
                ).value = response.razorpay_order_id;

                verificationForm.querySelector(
                    '[name="razorpay_signature"]'
                ).value = response.razorpay_signature;


                // Send payment details to Flask backend
                verificationForm.submit();

            },


            // ==========================================
            // 6. CHECKOUT CLOSE HANDLER
            // ==========================================

            modal: {

                ondismiss: function () {

                    payButton.disabled = false;

                    payButton.innerHTML =
                        'Pay <i class="fa-solid fa-arrow-right"></i>';

                    showMessage(
                        "Payment window closed. You can try again."
                    );

                }

            }

        };


        // Create Razorpay Checkout
        const razorpayCheckout = new Razorpay(options);


        // ==========================================
        // 7. PAYMENT FAILURE HANDLER
        // ==========================================

        razorpayCheckout.on("payment.failed", function (response) {

            payButton.disabled = false;

            payButton.innerHTML =
                'Pay <i class="fa-solid fa-arrow-right"></i>';

            const errorMessage =
                response.error.description || "Payment failed. Please try again.";

            showMessage(errorMessage);

        });


        // Open Checkout Popup
        try {

            razorpayCheckout.open();

        } catch (error) {

            console.error("Checkout Error:", error);

            payButton.disabled = false;

            payButton.innerHTML =
                'Pay <i class="fa-solid fa-arrow-right"></i>';

            showMessage("Unable to open payment gateway. Please try again.");

        }

    });

});
