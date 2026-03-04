import { Component, signal } from '@angular/core';
import { Tablero } from './tablero/tablero';


@Component({
  selector: 'app-root',
  imports: [Tablero],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App {
  protected readonly title = signal('angular-frontend');
  Movements: Record<string, string[]> = {
    // Peones (Fila 2)
    "a2": ["a3", "a4"],
    "b2": ["b3", "b4"],
    "c2": ["c3", "c4"],
    "d2": ["d3", "d4"],
    "e2": ["e3", "e4"],
    "f2": ["f3", "f4"],
    "g2": ["g3", "g4"],
    "h2": ["h3", "h4"],
    "b1": ["a3", "c3"],
    "g1": ["f3", "h3"]
  }
}
