class CourseSelector {
    private courses: string[] = ['Course 1', 'Course 2', 'Course 3', 'Course 4'];
    private selectedCourse: string | null = null;

    render(): void {
        const selectElement = document.createElement('select');
        this.courses.forEach(course => {
            const option = document.createElement('option');
            option.value = course;
            option.textContent = course;
            selectElement.appendChild(option);
        });

        selectElement.addEventListener('change', (event) => {
            this.selectedCourse = (event.target as HTMLSelectElement).value;
        });

        document.body.appendChild(selectElement);
    }

    getSelectedCourse(): string | null {
        return this.selectedCourse;
    }
}

export default CourseSelector;