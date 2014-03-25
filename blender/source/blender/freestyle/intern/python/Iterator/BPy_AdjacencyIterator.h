/*
 * ***** BEGIN GPL LICENSE BLOCK *****
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file source/blender/freestyle/intern/python/Iterator/BPy_AdjacencyIterator.h
 *  \ingroup freestyle
 */

#ifndef __FREESTYLE_PYTHON_ADJACENCYITERATOR_H__
#define __FREESTYLE_PYTHON_ADJACENCYITERATOR_H__

#include "../../stroke/ChainingIterators.h"
#include "../BPy_Iterator.h"


#ifdef __cplusplus
extern "C" {
#endif

///////////////////////////////////////////////////////////////////////////////////////////

#include <Python.h>

extern PyTypeObject AdjacencyIterator_Type;

#define BPy_AdjacencyIterator_Check(v) (PyObject_IsInstance((PyObject *)v, (PyObject *)&AdjacencyIterator_Type))

/*---------------------------Python BPy_AdjacencyIterator structure definition----------*/
typedef struct {
	BPy_Iterator py_it;
	AdjacencyIterator *a_it;
	bool at_start;
} BPy_AdjacencyIterator;

///////////////////////////////////////////////////////////////////////////////////////////

#ifdef __cplusplus
}
#endif

#endif /* __FREESTYLE_PYTHON_ADJACENCYITERATOR_H__ */
