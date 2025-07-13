// app/static/js/script.js
document.addEventListener('DOMContentLoaded', function () {

    function standardizeNameClient(value) {
        if (!value) return '';
        let cleanedValue = '';
        for (let i = 0; i < value.length; i++) {
            let char = value[i];
            if (/[a-zA-Z0-9\u00C0-\u00FF&.\- ]/.test(char)) {
                cleanedValue += char;
            }
        }
        return cleanedValue.replace(/\s+/g, ' ').toUpperCase();
    }

    function formatNumericInput(inputElement) {
        if (!inputElement) return;
        inputElement.addEventListener('input', function () {
            this.value = this.value.replace(/[^0-9.,]/g, '');
            this.value = this.value.replace(/,/g, '.');
            const parts = this.value.split('.');
            if (parts.length > 2) {
                this.value = parts[0] + '.' + parts.slice(1).join('');
            }
        });
        inputElement.addEventListener('blur', function () {
            let value = parseFloat(this.value);
            if (isNaN(value) || value < 0) {
            }
        });
    }

    const nomeInputs = [
        document.getElementById('nome'),
        document.getElementById('nome_banco'),
        document.getElementById('transacao'),
        document.getElementById('crediario'),
        document.getElementById('grupo'),
        document.getElementById('descricao'),
        document.getElementById('despesa_receita')
    ];
    nomeInputs.forEach(input => {
        if (input && !input.readOnly) {
            input.addEventListener('input', function () {
                this.value = standardizeNameClient(this.value);
            });
        }
    });

    const emailInput = document.getElementById('email');
    if (emailInput) {
        emailInput.addEventListener('input', function () {
            this.value = this.value.toLowerCase();
        });
    }

    const agenciaInput = document.getElementById('agencia');
    if (agenciaInput) {
        agenciaInput.addEventListener('input', function () {
            this.value = this.value.replace(/\D/g, '');
            if (this.value.length > 4) {
                this.value = this.value.slice(0, 4);
            }
        });
    }

    const contaNumInput = document.getElementById('conta');
    if (contaNumInput) {
        contaNumInput.addEventListener('input', function () {
            this.value = this.value.replace(/\D/g, '');
        });
    }

    const finalCrediarioInput = document.getElementById('final');
    if (finalCrediarioInput) {
        finalCrediarioInput.addEventListener('input', function () {
            this.value = this.value.replace(/\D/g, '');
            if (this.value.length > 4) {
                this.value = this.value.slice(0, 4);
            }
        });
    }

    const saldoInicialInput = document.getElementById('saldo_inicial');
    const limiteInput = document.getElementById('limite');
    const valorInput = document.getElementById('valor');

    if (saldoInicialInput) {
        formatNumericInput(saldoInicialInput);
    }
    if (limiteInput) {
        formatNumericInput(limiteInput);
    }
    if (valorInput) {
        formatNumericInput(valorInput);
    }

    // Lógica do submenu da sidebar
    const submenuToggles = document.querySelectorAll('.submenu-toggle');

    submenuToggles.forEach(toggle => {
        toggle.addEventListener('click', function (e) {
            e.preventDefault();
            const parentLi = this.closest('li.has-submenu');
            const submenu = parentLi.querySelector('.submenu');
            const arrow = this.querySelector('.submenu-arrow');

            if (submenu.style.display === 'block') {
                submenu.style.display = 'none';
                arrow.style.transform = 'rotate(0deg)';
                parentLi.classList.remove('active-parent');
            } else {
                document.querySelectorAll('.submenu').forEach(sub => {
                    if (sub !== submenu) sub.style.display = 'none';
                });
                document.querySelectorAll('.submenu-arrow').forEach(arr => {
                    if (arr !== arrow) arr.style.transform = 'rotate(0deg)';
                });
                document.querySelectorAll('.has-submenu').forEach(parent => {
                    if (parent !== parentLi) parent.classList.remove('active-parent');
                });

                submenu.style.display = 'block';
                arrow.style.transform = 'rotate(90deg)';
                parentLi.classList.add('active-parent');
            }
        });

        const parentLi = toggle.closest('li.has-submenu');
        const submenu = parentLi.querySelector('.submenu');
        const activeSubmenuItem = submenu.querySelector('a.active');
        if (activeSubmenuItem) {
            submenu.style.display = 'block';
            toggle.querySelector('.submenu-arrow').style.transform = 'rotate(90deg)';
            parentLi.classList.add('active-parent');
        }
    });
});
