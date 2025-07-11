/* app/static/js/script.js */

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
        document.getElementById('crediario')
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

    if (saldoInicialInput) {
        formatNumericInput(saldoInicialInput);
    }
    if (limiteInput) {
        formatNumericInput(limiteInput);
    }
});
