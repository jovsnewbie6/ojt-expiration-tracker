class YearSelector {
    private selectedYear: string;

    constructor() {
        this.selectedYear = '';
    }

    render(): void {
        const years = ['1st Year', '2nd Year', '3rd Year', '4th Year'];
        const dropdown = document.createElement('select');

        years.forEach(year => {
            const option = document.createElement('option');
            option.value = year;
            option.textContent = year;
            dropdown.appendChild(option);
        });

        dropdown.addEventListener('change', (event) => {
            this.selectedYear = (event.target as HTMLSelectElement).value;
        });

        document.body.appendChild(dropdown);
    }

    getSelectedYear(): string {
        return this.selectedYear;
    }
}

export default YearSelector;