export class Student {
    name: string;
    course: string;
    year: number;
    expirationDate: Date;

    constructor(name: string, course: string, year: number, expirationDate: Date) {
        this.name = name;
        this.course = course;
        this.year = year;
        this.expirationDate = expirationDate;
    }

    getStudentDetails(): string {
        return `Name: ${this.name}, Course: ${this.course}, Year: ${this.year}, Expiration Date: ${this.expirationDate.toDateString()}`;
    }

    isExpired(): boolean {
        const today = new Date();
        return this.expirationDate < today;
    }
}