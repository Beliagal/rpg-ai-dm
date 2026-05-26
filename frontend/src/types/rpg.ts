/**
 * Representa un objeto individual dentro del inventario del personaje.
 * Mapea directamente con ItemMutationSchema del backend.
 */
export interface InventoryItem {
  name: string;
  quantity: number;
  type: 'weapon' | 'light_armor' | 'heavy_armor' | 'shield' | 'potion' | 'utility' | string;
  equipped: boolean;
  properties?: Record<string, unknown>;
}

/**
 * Atributos y características base del personaje (SRD 5e).
 */
export interface CharacterStats {
  strength: number;
  dexterity: number;
  constitution: number;
  intelligence: number;
  wisdom: number;
  charisma: number;
}

/**
 * Modelo completo del personaje persistido en la base de datos.
 */
export interface Character {
  id: number;
  name: string;
  race: string;
  char_class: string;
  hp: number;
  max_hp: number;
  location: string;
  stats: CharacterStats;
  inventory: InventoryItem[];
}

/**
 * Contrato de datos requerido por el endpoint /narrate.
 */
export interface ChatMessagePayload {
  character_id: number;
  role: 'user' | 'assistant';
  content: string;
}

/**
 * Respuesta limpia devuelta por el controlador de narrativa.
 */
export interface NarrateResponse {
  response: string;
}