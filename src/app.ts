import { CourseSelector } from './components/courseSelector';
import { YearSelector } from './components/yearSelector';
import { ExpirationList } from './components/expirationList';

class App {
    private courseSelector: CourseSelector;
    private yearSelector: YearSelector;
    private expirationList: ExpirationList;

    constructor() {
        this.courseSelector = new CourseSelector();
        this.yearSelector = new YearSelector();
        this.expirationList = new ExpirationList();
    }

    public init(): void {
        this.render();
    }

    private render(): void {
        const appContainer = document.getElementById('app');
        if (appContainer) {
            appContainer.appendChild(this.courseSelector.render());
            appContainer.appendChild(this.yearSelector.render());
            appContainer.appendChild(this.expirationList.displayExpirations());
        }
    }
}

const app = new App();
app.init();