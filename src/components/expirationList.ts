export class ExpirationList {
    private expirations: { studentName: string; expirationDate: Date }[] = [];

    addExpiration(studentName: string, expirationDate: Date) {
        this.expirations.push({ studentName, expirationDate });
    }

    displayExpirations(): string {
        if (this.expirations.length === 0) {
            return "No expiration dates available.";
        }

        return this.expirations
            .map(expiration => `${expiration.studentName}: ${expiration.expirationDate.toLocaleDateString()}`)
            .join("\n");
    }
}