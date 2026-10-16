import {describe,it,expect} from 'vitest';
import {cartKey,cartTotal,useCart} from './cart';
import {money} from './types';
import type {Item} from './types';
const item:Item={id:'rice',name:'Jollof',description:'Rice',price:650000,image:'',available:true,featured:true,category_id:'c',location_id:'l',modifiers:[{id:'chicken',name:'Chicken',price:250000,available:true}]};
describe('shopping bag',()=>{
 it('treats reordered modifier selections as the same line',()=>{expect(cartKey('rice',['a','b'])).toBe(cartKey('rice',['b','a']));});
 it('includes modifiers and quantity in the estimate',()=>{useCart.getState().clear();useCart.getState().add(item,['chicken'],2);expect(cartTotal(useCart.getState().lines)).toBe(1800000);});
 it('merges matching selections, caps quantity, and supports removal',()=>{useCart.getState().clear();useCart.getState().add(item,[],19);useCart.getState().add(item,[],5);expect(useCart.getState().lines[0].quantity).toBe(20);useCart.getState().quantity(cartKey('rice',[]),0);expect(useCart.getState().lines).toHaveLength(0);});
 it('formats integer kobo without losing fractional naira',()=>{expect(money(150050)).toContain('1,500.50');});
});
