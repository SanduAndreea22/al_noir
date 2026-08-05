document.addEventListener('DOMContentLoaded', () => {
  const priceInputs = document.querySelectorAll('input[data-price]');
  const menuTotal = document.getElementById('menu-total');
  const advanceTotal = document.getElementById('advance-total');

  const updateDeposit = () => {
    const total = Array.from(priceInputs)
      .filter((input) => input.checked)
      .reduce((sum, input) => sum + Number.parseFloat(input.dataset.price || '0'), 0);
    menuTotal.textContent = `${total.toFixed(2)} lei`;
    advanceTotal.textContent = `${(total * 0.10).toFixed(2)} lei`;
  };

  priceInputs.forEach((input) => input.addEventListener('change', updateDeposit));
  updateDeposit();
});
