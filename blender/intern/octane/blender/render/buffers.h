/*
 * Copyright 2011, Blender Foundation.
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
 */

#ifndef __BUFFERS_H__
#define __BUFFERS_H__

#include "util_string.h"
#include "util_types.h"

OCT_NAMESPACE_BEGIN

class RenderServer;

class BufferParams {
public:
	BufferParams();

	bool modified(const BufferParams& params);

    // Offset into and width/height of the full buffer
	int offset_x;
	int offset_y;
	int full_width;
	int full_height;
};

class DisplayBuffer {
public:
	DisplayBuffer(RenderServer *server);
	~DisplayBuffer();

	void reset(BufferParams& params);
    void write(const string& filename);

	bool draw(RenderServer *server);

	BufferParams params;
	bool transparent;
    uchar4* rgba;

protected:
	void free();

	RenderServer *server;
};

OCT_NAMESPACE_END

#endif /* __BUFFERS_H__ */

