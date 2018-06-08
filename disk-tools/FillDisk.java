import java.io.*;

/**
 * Fill up a disk with a file of the given name.
 * Run without parameters to see usage.
 */
public class FillDisk {
  public static void main(String[] args) throws Exception {
    if (args.length == 2) {
      final File f = new File(args[0]);
      System.out.println("Creating filler file " + f);
      final FileOutputStream fos = new FileOutputStream(f.toString());
      final int blockSize = Integer.parseInt(args[1]);
      final byte[] buffer = new byte[blockSize];
      try {
        while (true) {
          fos.write(buffer);
          fos.getFD().sync();
        }
      } finally {
        fos.close();
      }
    } else {
      System.err.println("Usage: FillDisk <file> <block-size>");
    }
  }
}
