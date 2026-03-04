import { Component, input, computed } from '@angular/core';
import { NgClass } from '@angular/common';
import { CdkDrag, DragDropModule, CdkDragDrop, CdkDropList, CdkDropListGroup } from '@angular/cdk/drag-drop'

@Component({
  selector: 'app-tablero',
  standalone: true,
  templateUrl: './tablero.html',
  styleUrl: './tablero.css',
  imports: [NgClass, CdkDrag, DragDropModule, CdkDropList],
})
export class Tablero {
  
  //Vamos a tener una propiedad donde vamos a guadar la información de la posición que clickee
  SelectedSquare: {i: number, j: number} | null = null;

  //Vamos a crear una propiedad para referenciar la casilla de salida
  SelectedToSquare: {i: number, j: number} | null = null;

  //Posible Squares to move from the selected square
  SquaresToMove: string[] = [];

  //Este es el Input de el listado de movimientos y también es de tipo señal
  PossibleMoves = input.required<Record<string, string[]>>();

  //Este el FenString que representa el juego, esto es un input y este tipo SEÑAL
  FenString = input.required<string>();

  //Este es el FenBoard que es un array que representa el estado del juego visualmente 
  FenBoard = computed(() => {
    const fen = this.FenString();
    if(!fen){
      return [];
    }
    return this.generarTablero(this.FenString());
  })

  //Funcion para generar el tablero
  generarTablero(fenstring: string): string[][]{
    //Primero separemos por espacio
    let fenstringPartition = fenstring.split(" ");
    let FenBoard = []
    const FenColumns = fenstringPartition[0].split("/")
    for(const column of FenColumns){
      const RowArray: Array<string> = []
      for(const value of column){
        const num: number = parseInt(value)
        if(isNaN(num)){
          console.log("El valor ingresado no es un número valido");
          //Aqui estamos agregando las letras a la representación en matriz del tablero
          RowArray.push(value);
        }else{
          for(let i = 0; i < num; i++){
            RowArray.push(" ");
          }
        }
      }
      FenBoard.push(RowArray)
    }
    console.log(FenBoard)
    return FenBoard 
  }  

  //Funcion para lograr generar la posición de la ficha en el tablero
  getClasses(i: number, j: number){
    return {
      ["casilla"]: true,
      ["from"]: this.getFrom(i, j),
      ["to"]: this.getTo(i,j)
    }
  }

  getTo(i: number, j: number): Boolean{
    if(this.SelectedToSquare){
      if(this.SelectedToSquare.i === i && this.SelectedToSquare.j === j){
        return true;
      }else{
        return false;
      }
    }else{
      return false;
    }
  }


  getFrom(i: number, j: number): Boolean{
    if(this.SelectedSquare){
      if(this.SelectedSquare.i === i && this.SelectedSquare.j === j){
        return true;
      }else{
        return false;
      }
    }else{
      return false;
    }
  }


  //Funcion para generar a partir de las posiciones numericas el string de la posicion
  generatePosition(i: number, j: number): string{
    return 'abcdefgh'[j] + (8 - i)
  }

  verifyTo(i: number, j: number): Boolean{
    const StrPos = this.generatePosition(i, j);
    if(this.SquaresToMove.includes(StrPos)){
      return true;
    }else{
      return false;
    }
  }

  //Función que al hacer click selecciona la casilla cómo escogida, pero sólo si la casilla es distinta de vacia
  selectSquare(i: number, j: number): void{   
    if(this.SelectedSquare && this.verifyTo(i, j)){
      //Se asigna SelectedToSquare a {i, j}
      this.SelectedToSquare = {i, j};
      
      //La lógica de Movimiento de la Ficha
      console.log("Vamos a realizar un movimiento a esta ficha");
    }      
    //Calculamos la posición en string
    const StrPos = this.generatePosition(i, j);
    //Hago la asignación de las posiciones a la variable SelectedSquare
    this.SelectedSquare = {i, j}
    //Verificamos sí hay movimientos legales para hacer
    if(Object.entries(this.PossibleMoves()).length !== 0 && StrPos in this.PossibleMoves()){
        //Hemos encontrado que a partir de la casilla seleccionada se pueden realizar movimientos 
      this.SquaresToMove = this.PossibleMoves()[StrPos];
      console.log(this.SquaresToMove);
    } 
  }  
  
  //-- ACTUALIZACION DE TABLERO BOARD Y FENSTRING --
  //Función para actualizar el tablero de Ajedrez
  actualizarTablero(origin: string, destination: string): void{
    //Que hacer aqui
  }

  //Metodo para dropear la pieza
  drop(e: CdkDragDrop<any>): void{
    console.log("Hola en proceso");

    const origin = e.previousContainer.id;
    const destination = e.container.id
    
    //Realizamos la actualizacion
    this.actualizarTablero(origin, destination)
  }
}
