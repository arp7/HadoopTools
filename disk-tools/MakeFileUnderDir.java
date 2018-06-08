import java.io.*;
import java.util.Random;

/**
 * Keep making 1 byte files under the given directory forever,
 * until the FileSystem runs out of resources.
 * File names are generated randomly.
 */
public class MakeFileUnderDir {
  public static void main(String[] args) throws Exception {
    int fileIndex = 0;
    final Random r = new Random();
    final int randPrefix = Math.abs(r.nextInt());
    final File dir = new File(args[0]);

    while (true) {
      final String filename = "file-" + randPrefix + "-" + fileIndex++;
      final File f = new File(dir, filename);
      System.out.println("Creating file " + f);
      final FileOutputStream fos = new FileOutputStream(f.toString());
      fos.write(new byte[1]);
      fos.getFD().sync();
      fos.close();
    }
  }
}
