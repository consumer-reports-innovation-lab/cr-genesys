
import { NextRequest, NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';

let prisma: PrismaClient | null = null;

if (typeof window === 'undefined') {
  try {
    prisma = new PrismaClient();
  } catch (error) {
    console.error("Failed to initialize Prisma:", error);
  }
}

export async function DELETE(request: NextRequest) {
  if (!prisma) {
    return NextResponse.json({ error: 'Prisma client not initialized' }, { status: 500 });
  }

  const { searchParams } = new URL(request.url);
  const deviceId = searchParams.get('deviceId');

  if (!deviceId) {
    return NextResponse.json({ error: 'deviceId is required' }, { status: 400 });
  }

  try {
    const deleteResult = await prisma.session.deleteMany({
      where: {
        deviceId: deviceId,
      },
    });

    if (deleteResult.count === 0) {
      return NextResponse.json({ message: 'No sessions found for this deviceId' }, { status: 404 });
    }

    return NextResponse.json({ message: `Successfully deleted ${deleteResult.count} sessions` }, { status: 200 });
  } catch (error) {
    console.error('Failed to delete sessions by deviceId:', error);
    return NextResponse.json({ error: 'Failed to delete sessions' }, { status: 500 });
  }
}
